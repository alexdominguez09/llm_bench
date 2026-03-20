#!/usr/bin/env python3
"""
LLM Benchmark - A comprehensive benchmarking tool for LLM inference servers.
Supports OpenAI-compatible APIs including llama.cpp, Ollama, and other backends.
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from typing import Literal

import httpx
from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
import yaml


@dataclass
class BenchmarkResult:
    """Single benchmark test result."""
    test_name: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    ttft: float  # Time to first token (seconds)
    total_time: float  # Total response time (seconds)
    tps: float  # Tokens per second
    stream: bool
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class BenchmarkConfig(BaseModel):
    """Benchmark configuration."""
    base_url: str = "http://192.168.1.14:11434/v1"
    api_key: str = "no-key-required"
    model: str = "Qwen3.5-35B-A3B-Q8_0"
    
    # Benchmark settings
    output_tokens: List[int] = Field(default_factory=lambda: [100, 200, 500])
    prompt_lengths: List[int] = Field(default_factory=lambda: [50, 200, 500])
    iterations: int = 3
    stream: bool = True
    temperature: float = 0.7
    top_p: float = 0.9
    
    # Timeout settings
    timeout: float = 300.0
    
    # Output settings
    output_dir: str = "results"
    save_json: bool = True
    verbose: bool = True


class LLMBenchmark:
    """Main benchmarking class for LLM inference servers."""
    
    # Test prompts for different scenarios
    TEST_PROMPTS = {
        "short": "What is the capital of France?",
        "medium": "Explain the concept of machine learning and its applications in modern technology.",
        "long": """Artificial intelligence has transformed numerous industries in recent years. 
Machine learning, a subset of AI, enables systems to learn and improve from experience without being explicitly programmed.
Deep learning, powered by neural networks, has achieved remarkable breakthroughs in image recognition, natural language processing, and game playing.
This technology is being applied in healthcare for diagnostic imaging, in finance for fraud detection, in autonomous vehicles for perception,
and in countless other domains. The rapid advancement of AI raises important questions about ethics, safety, and the future of work.
As we move forward, it's crucial to develop AI systems that are reliable, fair, and beneficial to humanity.""",
        "coding": "Write a Python function that implements merge sort algorithm with detailed comments explaining each step.",
        "math": "Calculate the derivative of f(x) = 3x^2 + 2x - 5 and explain the process.",
        "creative": "Write a short science fiction story about humanity's first contact with an alien civilization.",
    }
    
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.base_url,
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=httpx.Timeout(config.timeout)
        )
        self.results: List[BenchmarkResult] = []
        self.console = Console()
        
    async def check_connection(self) -> bool:
        """Check if the LLM server is reachable."""
        try:
            # Remove /v1 from the end if present to avoid double /v1
            base = self.config.base_url.rstrip("/")
            response = await self.client.get(f"{base}/models", timeout=10.0)
            if response.status_code == 200:
                models = response.json()
                model_names = [m.get("id", m.get("model", "")) for m in models.get("data", [])]
                self.console.print(f"[green]✓ Connected to server at {self.config.base_url}")
                self.console.print(f"[cyan]Available models: {', '.join(model_names[:5])}{'...' if len(model_names) > 5 else ''}")
                return True
            else:
                self.console.print(f"[red]✗ Server returned status {response.status_code}")
                return False
        except Exception as e:
            self.console.print(f"[red]✗ Connection failed: {e}")
            return False
    
    async def count_tokens(self, text: str) -> int:
        """Estimate token count using character-based approximation.
        For accurate tokenization, you'd need the model's tokenizer.
        Rough estimate: 1 token ≈ 4 characters for English text.
        """
        # This is a rough estimate - for accurate counts, use the model's tokenizer
        return len(text) // 4 + 1
    
    async def run_completion(self, prompt: str, max_tokens: int, stream: bool = False) -> tuple[BenchmarkResult, Optional[httpx.Response]]:
        """Run a single completion request and measure performance."""
        start_time = time.perf_counter()
        ttft = None
        total_tokens = 0
        completion_tokens = 0
        
        try:
            # Remove /v1 from the end if present to avoid double /v1
            base = self.config.base_url.rstrip("/")
            response = await self.client.post(
                f"{base}/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "stream": stream,
                    "temperature": self.config.temperature,
                    "top_p": self.config.top_p,
                }
            )
            
            if response.status_code != 200:
                error_msg = f"Server error: {response.status_code} - {response.text[:100]}"
                return BenchmarkResult(
                    test_name="",
                    model=self.config.model,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    ttft=0,
                    total_time=time.perf_counter() - start_time,
                    tps=0,
                    stream=stream,
                    error=error_msg
                ), response
            
            if stream:
                # Streaming mode
                ttft_start = time.perf_counter()
                async for chunk in response.aiter_lines():
                    if ttft is None and chunk.strip():
                        ttft = time.perf_counter() - ttft_start
                    if chunk.startswith("data: "):
                        data = chunk[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(data)
                            choice = chunk_data.get("choices", [{}])[0]
                            delta = choice.get("delta", {})
                            # llama.cpp returns reasoning_content, standard API returns content
                            content = delta.get("content") or delta.get("reasoning_content", "")
                            completion_tokens += len(content) // 4
                        except json.JSONDecodeError:
                            pass
            else:
                # Non-streaming mode
                data = response.json()
                completion_tokens = data.get("usage", {}).get("completion_tokens", 0)
                ttft = time.perf_counter() - start_time
            
            total_time = time.perf_counter() - start_time
            prompt_tokens = await self.count_tokens(prompt)
            total_tokens = prompt_tokens + completion_tokens
            tps = completion_tokens / total_time if total_time > 0 else 0
            
            return BenchmarkResult(
                test_name="",
                model=self.config.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                ttft=ttft or total_time,
                total_time=total_time,
                tps=tps,
                stream=stream
            ), response
            
        except Exception as e:
            return BenchmarkResult(
                test_name="",
                model=self.config.model,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                ttft=0,
                total_time=time.perf_counter() - start_time,
                tps=0,
                stream=stream,
                error=str(e)
            ), None
    
    def generate_prompt(self, length: int, scenario: str = "medium") -> str:
        """Generate a prompt of approximately the specified length."""
        base_prompt = self.TEST_PROMPTS.get(scenario, self.TEST_PROMPTS["medium"])
        
        if len(base_prompt) >= length:
            return base_prompt[:length]
        
        # Pad the prompt to reach desired length
        padding = " The quick brown fox jumps over the lazy dog. "
        while len(base_prompt) < length:
            base_prompt += padding
        
        return base_prompt[:length]
    
    async def run_test(self, test_name: str, prompt: str, output_tokens: int, stream: bool, iteration: int) -> BenchmarkResult:
        """Run a single test iteration."""
        result, _ = await self.run_completion(prompt, output_tokens, stream=stream)
        result.test_name = f"{test_name}_iter{iteration}"
        return result
    
    async def run_benchmark(self) -> List[BenchmarkResult]:
        """Run the full benchmark suite."""
        if not await self.check_connection():
            self.console.print("[bold red]Cannot connect to server. Exiting.")
            return []
        
        self.console.print(Panel.fit("[bold cyan]Starting LLM Benchmark[/bold cyan]", style="cyan"))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            # Warmup run
            task = progress.add_task("[cyan]Warming up model...", total=1)
            await self.run_test("warmup", self.TEST_PROMPTS["medium"], 10, stream=False, iteration=0)
            progress.update(task, completed=1)
            
            # Run all tests
            test_tasks = []
            
            scenarios = list(self.TEST_PROMPTS.keys())
            for scenario in scenarios:
                for length in self.config.prompt_lengths:
                    prompt = self.generate_prompt(length, scenario)
                    for output_tokens in self.config.output_tokens:
                        for iteration in range(self.config.iterations):
                            test_name = f"{scenario}_{length}chars_{output_tokens}tokens"
                            task = progress.add_task(
                                f"[cyan]Running {test_name}...",
                                total=self.config.iterations
                            )
                            test_tasks.append((test_name, prompt, output_tokens, self.config.stream, iteration))
                            progress.update(task, completed=iteration + 1)
            
            # Execute all tests
            for test_name, prompt, output_tokens, stream, iteration in test_tasks:
                result = await self.run_test(test_name, prompt, output_tokens, stream, iteration)
                self.results.append(result)
                
                if self.config.verbose:
                    status = "[green]✓" if result.error is None else "[red]✗"
                    self.console.print(f"{status} {test_name}: {result.tps:.2f} tps, "
                                     f"TTFT: {result.ttft:.3f}s, Time: {result.total_time:.2f}s")
            
            progress.refresh()
        
        return self.results
    
    def display_results(self):
        """Display benchmark results in a formatted table."""
        if not self.results:
            self.console.print("[yellow]No results to display.")
            return
        
        # Create results table
        table = Table(title="LLM Benchmark Results")
        table.add_column("Test", style="cyan")
        table.add_column("Model", style="green")
        table.add_column("Prompt Tokens", justify="right")
        table.add_column("Completion Tokens", justify="right")
        table.add_column("Total Tokens", justify="right")
        table.add_column("TTFT (s)", justify="right")
        table.add_column("Total Time (s)", justify="right")
        table.add_column("Tokens/sec", justify="right")
        table.add_column("Stream", justify="center")
        
        for result in self.results:
            error_indicator = f" [red]✗ {result.error}[/red]" if result.error else ""
            table.add_row(
                result.test_name,
                result.model,
                str(result.prompt_tokens),
                str(result.completion_tokens),
                str(result.total_tokens),
                f"{result.ttft:.3f}",
                f"{result.total_time:.2f}",
                f"{result.tps:.2f}",
                "✓" if result.stream else "✗",
            )
        
        self.console.print(table)
        
        # Summary statistics
        successful_results = [r for r in self.results if r.error is None]
        if successful_results:
            self.console.print("\n[bold]Summary Statistics:[/bold]")
            avg_tps = sum(r.tps for r in successful_results) / len(successful_results)
            avg_ttft = sum(r.ttft for r in successful_results) / len(successful_results)
            avg_time = sum(r.total_time for r in successful_results) / len(successful_results)
            
            self.console.print(f"  Average Tokens/Second: {avg_tps:.2f}")
            self.console.print(f"  Average TTFT: {avg_ttft:.3f}s")
            self.console.print(f"  Average Total Time: {avg_time:.2f}s")
            self.console.print(f"  Total Tests Run: {len(self.results)}")
            self.console.print(f"  Successful Tests: {len(successful_results)}")
    
    def save_results(self, results: Optional[List[BenchmarkResult]] = None):
        """Save results to JSON file."""
        if not results:
            results = self.results
        
        if not results:
            return
        
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"
        filepath = output_dir / filename
        
        # Convert results to serializable format
        data = {
            "config": self.config.model_dump(),
            "timestamp": datetime.now().isoformat(),
            "results": [
                {
                    "test_name": r.test_name,
                    "model": r.model,
                    "prompt_tokens": r.prompt_tokens,
                    "completion_tokens": r.completion_tokens,
                    "total_tokens": r.total_tokens,
                    "ttft": r.ttft,
                    "total_time": r.total_time,
                    "tps": r.tps,
                    "stream": r.stream,
                    "error": r.error,
                    "timestamp": r.timestamp,
                }
                for r in results
            ]
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        self.console.print(f"\n[green]✓ Results saved to {filepath}")


async def main():
    """Main entry point for the benchmark script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="LLM Benchmark - Benchmark LLM inference servers",
        epilog="Examples:\n"
               "  python benchmark.py --benchmark_type speed\n"
               "  python benchmark.py --benchmark_type tool_call\n"
               "  python benchmark.py --benchmark_type speed --output-tokens 100 200 500\n"
               "  python benchmark.py --benchmark_type tool_call --iterations 5"
    )
    
    # Benchmark type selection
    parser.add_argument("--benchmark_type", "-t", 
                       choices=["speed", "tool_call", "all"],
                       default="all",
                       help="Type of benchmark to run (default: all)")
    
    # Speed benchmark options
    parser.add_argument("--output-tokens", nargs="+", type=int, default=[100, 200, 500],
                       help="Number of output tokens to generate (space-separated)")
    parser.add_argument("--stream", action="store_true", default=True,
                       help="Enable streaming mode")
    parser.add_argument("--no-stream", action="store_true",
                       help="Disable streaming mode")
    
    # Common options
    parser.add_argument("--base-url", default="http://192.168.1.14:8080/v1",
                       help="Base URL of the LLM server")
    parser.add_argument("--api-key", default="no-key-required",
                       help="API key for the server")
    parser.add_argument("--model", default="Qwen3.5-35B-A3B-Q8_0",
                       help="Model name to benchmark")
    parser.add_argument("--iterations", type=int, default=3,
                       help="Number of iterations per test")
    parser.add_argument("--timeout", type=float, default=300.0,
                       help="Request timeout in seconds")
    parser.add_argument("--no-save", action="store_true",
                       help="Disable saving results to JSON")
    parser.add_argument("--output-dir", default="results",
                       help="Directory to save results")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Suppress verbose output")
    
    args = parser.parse_args()
    
    # Run speed benchmark
    if args.benchmark_type in ["speed", "all"]:
        print("\n" + "="*60)
        print("SPEED BENCHMARK")
        print("="*60)
        
        speed_config = BenchmarkConfig(
            base_url=args.base_url,
            api_key=args.api_key,
            model=args.model,
            output_tokens=args.output_tokens,
            iterations=args.iterations,
            stream=not args.no_stream if args.no_stream else args.stream,
            timeout=args.timeout,
            save_json=not args.no_save,
            output_dir=args.output_dir,
            verbose=not args.quiet
        )
        
        speed_benchmark = LLMBenchmark(speed_config)
        speed_results = await speed_benchmark.run_benchmark()
        speed_benchmark.display_results()
        
        if speed_config.save_json and speed_results:
            speed_benchmark.save_results(speed_results)
    
    # Run tool calling benchmark
    if args.benchmark_type in ["tool_call", "all"]:
        print("\n" + "="*60)
        print("TOOL CALLING BENCHMARK")
        print("="*60)
        
        try:
            from tool_benchmark import ToolBenchmark, ToolBenchmarkConfig
            
            tool_config = ToolBenchmarkConfig(
                base_url=args.base_url,
                api_key=args.api_key,
                model=args.model,
                iterations=args.iterations,
                save_json=not args.no_save,
                output_dir=args.output_dir,
                verbose=not args.quiet
            )
            
            tool_benchmark = ToolBenchmark(tool_config)
            tool_results = await tool_benchmark.run_benchmark()
            tool_benchmark.display_results()
            
            if tool_config.save_json and tool_results:
                tool_benchmark.save_results(tool_results)
                
        except ImportError as e:
            print(f"[red]Warning: Could not import tool_benchmark module: {e}")
            print("Run 'pip install -r requirements.txt' to ensure all dependencies are installed.")


if __name__ == "__main__":
    asyncio.run(main())
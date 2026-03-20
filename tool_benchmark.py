"""
LLM Tool-Calling Benchmark - Tests LLM's understanding and planning for MCP tools.
Since not all LLM servers support native tool calling, this benchmark tests:
1. The model's ability to identify when tools should be used
2. Parameter extraction from natural language
3. Multi-step tool planning
4. Tool selection accuracy
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import re

import httpx
from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
import yaml


class ToolCallType(Enum):
    """Types of tool calls for benchmarking."""
    SIMPLE = "simple"
    COMPLEX_PARAMS = "complex_params"
    MULTISTEP = "multistep"
    CONDITIONAL = "conditional"
    SEARCH = "search"
    FILESYSTEM = "filesystem"
    GITHUB = "github"
    MEMORY = "memory"
    WEB = "web"


@dataclass
class ToolBenchmarkResult:
    """Complete benchmark result for tool calling."""
    test_name: str
    model: str
    tool_type: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    ttft: float
    total_time: float
    tps: float
    tool_recommended: bool
    correct_tool: bool
    params_in_response: bool
    multi_step_plan: bool
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ToolBenchmarkConfig(BaseModel):
    """Tool benchmark configuration."""
    base_url: str = "http://192.168.1.14:11434/v1"
    api_key: str = "no-key-required"
    model: str = "Qwen3.5-35B-A3B-Q8_0"
    
    # Benchmark settings
    iterations: int = 3
    save_json: bool = True
    output_dir: str = "results"
    verbose: bool = True
    timeout: float = 300.0


# Available tools that the LLM should understand (comprehensive list)
AVAILABLE_TOOLS = [
    # Web Search Tools
    {"name": "brave_search_brave_web_search", "description": "Web search using Brave Search API for general queries, news, articles"},
    {"name": "brave_search_brave_local_search", "description": "Search for local businesses, restaurants, services with addresses and ratings"},
    
    # File System Operations
    {"name": "filesystem_read_text_file", "description": "Read file contents as text with encoding handling"},
    {"name": "filesystem_write_file", "description": "Create or overwrite file with new content"},
    {"name": "filesystem_edit_file", "description": "Make line-based edits to text file with git-style diff"},
    {"name": "filesystem_list_directory", "description": "Get detailed listing of files and directories"},
    {"name": "filesystem_search_files", "description": "Recursively search for files matching pattern"},
    {"name": "filesystem_create_directory", "description": "Create directory or ensure it exists"},
    {"name": "filesystem_move_file", "description": "Move or rename files and directories"},
    
    # GitHub Operations
    {"name": "github_search_code", "description": "Fast code search across ALL GitHub repositories"},
    {"name": "github_search_repositories", "description": "Find GitHub repositories by name, description, topics"},
    {"name": "github_search_issues", "description": "Search for issues in GitHub repositories"},
    {"name": "github_get_file_contents", "description": "Get contents of file or directory from GitHub"},
    {"name": "github_create_or_update_file", "description": "Create or update file in GitHub repository"},
    {"name": "github_list_issues", "description": "List issues in GitHub repository"},
    {"name": "github_create_pull_request", "description": "Create new pull request in GitHub repository"},
    {"name": "github_create_repository", "description": "Create new GitHub repository"},
    
    # Knowledge Graph / Memory
    {"name": "memory_create_entities", "description": "Create entities in knowledge graph"},
    {"name": "memory_add_observations", "description": "Add observations to entities"},
    {"name": "memory_search_nodes", "description": "Search for nodes in knowledge graph"},
    {"name": "memory_read_graph", "description": "Read entire knowledge graph"},
    
    # Documentation Search
    {"name": "context7_resolve-library-id", "description": "Resolve package/product name to Context7 library ID"},
    {"name": "context7_query-docs", "description": "Retrieve and query up-to-date documentation and code examples"},
    
    # Browser Automation
    {"name": "puppeteer_puppeteer_navigate", "description": "Navigate to URL in browser"},
    {"name": "puppeteer_puppeteer_screenshot", "description": "Take screenshot of page or specific element"},
    {"name": "puppeteer_puppeteer_click", "description": "Click element on page"},
    {"name": "puppeteer_puppeteer_fill", "description": "Fill out input field"},
    
    # Utility (most relevant)
    {"name": "everything_get-env", "description": "Returns environment variables for debugging"},
    {"name": "everything_get-structured-content", "description": "Returns structured content with output schema"},
]


class ToolBenchmark:
    """Benchmark tool understanding and planning capabilities."""
    
    TEST_SCENARIOS = {
        ToolCallType.SIMPLE: {
            "name": "Simple Tool Recommendation",
            "description": "Identify when a single tool should be used",
            "prompts": [
                "I need to find information about the latest AI research papers. What tool should I use?",
                "Can you help me search for Python tutorials online?",
                "I want to look up the definition of 'quantum computing'. What's the best approach?",
            ],
            "expected_tools": ["brave_search", "context7"],
        },
        ToolCallType.COMPLEX_PARAMS: {
            "name": "Complex Parameter Extraction",
            "description": "Extract multiple parameters from natural language",
            "prompts": [
                "Search for Python tutorials on YouTube, filter by 2024 videos, and show me the top 5 results. What parameters would you extract?",
                "Find GitHub repositories with more than 1000 stars in the Python language.",
                "Search for restaurants in San Francisco that serve Italian food with ratings above 4 stars.",
            ],
            "expected_tools": ["brave_search", "github_search", "github_search_repositories"],
        },
        ToolCallType.MULTISTEP: {
            "name": "Multi-Step Tool Planning",
            "description": "Plan sequential tool calls",
            "prompts": [
                "I want to find the latest news about AI, then search for related research papers, and summarize the key findings. What's your plan?",
                "Search for a Python library, check its GitHub repository, and tell me about its contributors.",
                "Find information about climate change, search for recent studies, and identify the main conclusions.",
            ],
            "expected_tools": ["brave_search", "github_search", "context7", "filesystem"],
        },
        ToolCallType.CONDITIONAL: {
            "name": "Conditional Tool Selection",
            "description": "Choose tools based on conditions",
            "prompts": [
                "If there's a GitHub issue about this feature, find it; otherwise create a search for it.",
                "Check if this repository has recent activity, if yes show me the latest commits.",
                "Search for the file, and if found, read its contents.",
            ],
            "expected_tools": ["github_search", "brave_search", "filesystem"],
        },
        ToolCallType.SEARCH: {
            "name": "Web Search",
            "description": "Test search tool understanding",
            "prompts": [
                "Search for the latest developments in large language models.",
                "Find information about Python web development best practices in 2024.",
                "Search for recent benchmarks of open-source LLMs.",
            ],
            "expected_tools": ["brave_search", "context7"],
        },
        ToolCallType.FILESYSTEM: {
            "name": "Filesystem Operations",
            "description": "Test filesystem tool understanding",
            "prompts": [
                "List all Python files in the current directory.",
                "Find the README file and show me its contents.",
                "Search for files containing 'benchmark' in the name.",
            ],
            "expected_tools": ["filesystem_list", "filesystem_read", "filesystem_search"],
        },
        ToolCallType.GITHUB: {
            "name": "GitHub Operations",
            "description": "Test GitHub API understanding",
            "prompts": [
                "Find open issues in the modelcontextprotocol/servers repository.",
                "Search for pull requests from the last month in the github/copilot repository.",
                "List the top contributors to the llm-bench repository.",
            ],
            "expected_tools": ["github_search", "github_list_issues", "github_search_code"],
        },
        ToolCallType.MEMORY: {
            "name": "Memory Operations",
            "description": "Test memory tool understanding",
            "prompts": [
                "Store the following in memory: 'Meeting at 3pm tomorrow with the team.'",
                "Retrieve information about my scheduled meetings from memory.",
                "Save this note: 'Project deadline is next Friday.'",
            ],
            "expected_tools": ["memory_create", "memory_add", "memory_search"],
        },
        ToolCallType.WEB: {
            "name": "Web Automation",
            "description": "Test web scraping understanding",
            "prompts": [
                "Navigate to example.com and extract the main heading.",
                "Visit a news website and summarize the top story.",
                "Check the status page for any service outages.",
            ],
            "expected_tools": ["puppeteer", "brave_search"],
        },
    }
    
    def __init__(self, config: ToolBenchmarkConfig):
        self.config = config
        # Strip /v1 from base_url since we'll append endpoints manually
        base_url = config.base_url.rstrip("/").replace("/v1", "")
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=httpx.Timeout(config.timeout)
        )
        self.results: List[ToolBenchmarkResult] = []
        self.console = Console()
        
    async def check_connection(self) -> bool:
        """Check if the LLM server is reachable."""
        try:
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
        """Estimate token count."""
        return len(text) // 4 + 1
    
    async def analyze_tool_recommendation(self, prompt: str, response_content: str) -> Dict:
        """Analyze the model's response for tool-related content."""
        result = {
            "tool_recommended": False,
            "correct_tool": False,
            "params_in_response": False,
            "multi_step_plan": False,
        }
        
        # Check if any tool is mentioned
        tool_names = [t["name"] for t in AVAILABLE_TOOLS]
        response_lower = response_content.lower()
        
        # Extract tool keywords from tool names (remove namespace prefixes and underscores)
        tool_keywords = []
        for tool in AVAILABLE_TOOLS:
            # Extract meaningful parts from tool names
            name = tool["name"]
            # Remove namespace prefixes like "github_", "filesystem_", etc.
            simple_name = name.replace("github_", "").replace("filesystem_", "").replace("memory_", "").replace("brave_search_", "").replace("puppeteer_", "").replace("context7_", "").replace("everything_", "")
            # Split by underscores and add all parts as keywords
            parts = simple_name.split("_")
            tool_keywords.extend(parts)
            # Also add the full simple name
            tool_keywords.append(simple_name.replace("_", " "))
        
        # Check for tool mentions
        for keyword in tool_keywords:
            if keyword and len(keyword) > 2 and keyword in response_lower:
                result["tool_recommended"] = True
                break
        
        # Check for parameter patterns
        param_patterns = [
            r'parameter[s]?\s*[=:]\s*\w+',
            r'query\s*[=:]\s*["\']',
            r'path\s*[=:]\s*["\']',
            r'filter',
            r'sort',
            r'limit',
            r'offset',
            r'count\s*[=:]\s*\d+',
            r'top\s*\d+',
            r'first\s*\d+',
            r'language\s*[=:]\s*\w+',
            r'stars\s*[=:]\s*\d+',
            r'rating\s*[=:]\s*\d+',
        ]
        for pattern in param_patterns:
            if re.search(pattern, response_lower):
                result["params_in_response"] = True
                break
        
        # Check for multi-step planning
        multi_step_patterns = [
            r'first\s+then',
            r'step\s*1',
            r'next',
            r'after\s+that',
            r'plan.*step',
            r'workflow',
            r'sequence',
            r'first.*second',
            r'begin.*then',
            r'start.*follow',
        ]
        for pattern in multi_step_patterns:
            if re.search(pattern, response_lower, re.IGNORECASE):
                result["multi_step_plan"] = True
                break
        
        return result
    
    async def run_tool_call_test(self, prompt: str, scenario: ToolCallType, iteration: int) -> ToolBenchmarkResult:
        """Run a single tool calling test."""
        scenario_data = self.TEST_SCENARIOS[scenario]
        start_time = time.perf_counter()
        ttft = None
        completion_tokens = 0
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant with access to various tools. When someone asks for help, analyze their request and recommend the appropriate tool(s) to use. Explain your reasoning and any parameters you would extract."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Remove /v1 from the end if present to avoid double /v1
            base = self.config.base_url.rstrip("/")
            response = await self.client.post(
                f"{base}/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "max_tokens": 1000,
                    "stream": False,
                    "temperature": 0.7,
                    "top_p": 0.9,
                }
            )
            
            if response.status_code != 200:
                return ToolBenchmarkResult(
                    test_name=f"{scenario.value}_{iteration}",
                    model=self.config.model,
                    tool_type=scenario.value,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    ttft=0,
                    total_time=time.perf_counter() - start_time,
                    tps=0,
                    tool_recommended=False,
                    correct_tool=False,
                    params_in_response=False,
                    multi_step_plan=False,
                    error=f"Server error: {response.status_code}",
                    timestamp=datetime.now().isoformat()
                )
            
            data = response.json()
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content", "")
            completion_tokens = data.get("usage", {}).get("completion_tokens", 0)
            
            ttft = time.perf_counter() - start_time
            total_time = time.perf_counter() - start_time
            prompt_tokens = await self.count_tokens(prompt)
            total_tokens = prompt_tokens + completion_tokens
            tps = completion_tokens / total_time if total_time > 0 else 0
            
            # Analyze the response
            analysis = await self.analyze_tool_recommendation(prompt, content)
            
            # Check if recommended tool is correct
            expected_tools = scenario_data["expected_tools"]
            analysis["correct_tool"] = False
            if analysis["tool_recommended"]:
                # Check if any expected tool keyword matches any tool name
                for tool in AVAILABLE_TOOLS:
                    tool_name_lower = tool["name"].lower()
                    for expected in expected_tools:
                        # Check if expected tool keyword is in tool name
                        if expected in tool_name_lower:
                            analysis["correct_tool"] = True
                            break
                    if analysis["correct_tool"]:
                        break
            
            return ToolBenchmarkResult(
                test_name=f"{scenario.value}_{iteration}",
                model=self.config.model,
                tool_type=scenario.value,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                ttft=ttft,
                total_time=total_time,
                tps=tps,
                tool_recommended=analysis["tool_recommended"],
                correct_tool=analysis["correct_tool"],
                params_in_response=analysis["params_in_response"],
                multi_step_plan=analysis["multi_step_plan"],
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            return ToolBenchmarkResult(
                test_name=f"{scenario.value}_{iteration}",
                model=self.config.model,
                tool_type=scenario.value,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                ttft=0,
                total_time=time.perf_counter() - start_time,
                tps=0,
                tool_recommended=False,
                correct_tool=False,
                params_in_response=False,
                multi_step_plan=False,
                error=str(e),
                timestamp=datetime.now().isoformat()
            )
    
    async def run_benchmark(self) -> List[ToolBenchmarkResult]:
        """Run the full tool calling benchmark."""
        if not await self.check_connection():
            self.console.print("[bold red]Cannot connect to server. Exiting.")
            return []
        
        self.console.print(Panel.fit("[bold cyan]Starting Tool-Calling Benchmark[/bold cyan]", style="cyan"))
        self.console.print(f"\n[italic]Model: {self.config.model}[/italic]")
        self.console.print(f"[italic]Available tools: {len(AVAILABLE_TOOLS)}[/italic]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            scenarios = list(self.TEST_SCENARIOS.keys())
            total_tests = len(scenarios) * self.config.iterations
            
            task = progress.add_task("[cyan]Running tool-understanding benchmark...", total=total_tests)
            
            for scenario in scenarios:
                scenario_data = self.TEST_SCENARIOS[scenario]
                self.console.print(f"\n[bold yellow]Testing: {scenario_data['name']}[/bold yellow]")
                self.console.print(f"  {scenario_data['description']}")
                
                for iteration in range(self.config.iterations):
                    import random
                    prompt = random.choice(scenario_data["prompts"])
                    
                    result = await self.run_tool_call_test(prompt, scenario, iteration)
                    self.results.append(result)
                    
                    status = "[green]✓" if result.correct_tool else "[yellow]⚠" if result.tool_recommended else "[red]✗"
                    progress.update(task, advance=1)
                    
                    if self.config.verbose:
                        self.console.print(f"  {status} Iteration {iteration + 1}: "
                                         f"TPS: {result.tps:.2f}, "
                                         f"Tool Rec: {result.tool_recommended}, "
                                         f"Correct: {result.correct_tool}")
            
            progress.refresh()
        
        return self.results
    
    def display_results(self):
        """Display benchmark results."""
        if not self.results:
            self.console.print("[yellow]No results to display.")
            return
        
        # Group results by tool type
        results_by_type: Dict[str, List[ToolBenchmarkResult]] = {}
        for result in self.results:
            if result.tool_type not in results_by_type:
                results_by_type[result.tool_type] = []
            results_by_type[result.tool_type].append(result)
        
        # Display summary table
        table = Table(title="Tool-Understanding Benchmark Results")
        table.add_column("Test Type", style="cyan")
        table.add_column("Tool Rec", justify="center")
        table.add_column("Correct", justify="center")
        table.add_column("Params", justify="center")
        table.add_column("Multi-Step", justify="center")
        table.add_column("TTFT (s)", justify="right")
        table.add_column("TPS", justify="right")
        table.add_column("Success Rate", justify="right")
        
        for tool_type, type_results in results_by_type.items():
            total = len(type_results)
            recommended = sum(1 for r in type_results if r.tool_recommended)
            correct = sum(1 for r in type_results if r.correct_tool)
            params = sum(1 for r in type_results if r.params_in_response)
            multistep = sum(1 for r in type_results if r.multi_step_plan)
            successful = sum(1 for r in type_results if r.correct_tool)
            
            avg_ttft = sum(r.ttft for r in type_results if not r.error) / max(1, total - sum(1 for r in type_results if r.error))
            avg_tps = sum(r.tps for r in type_results if not r.error) / max(1, total - sum(1 for r in type_results if r.error))
            success_rate = (successful / total * 100) if total > 0 else 0
            
            table.add_row(
                tool_type,
                f"{recommended}/{total}",
                f"{correct}/{total}",
                f"{params}/{total}",
                f"{multistep}/{total}",
                f"{avg_ttft:.3f}" if avg_ttft else "N/A",
                f"{avg_tps:.2f}" if avg_tps else "N/A",
                f"{success_rate:.1f}%",
            )
        
        self.console.print(table)
        
        # Detailed statistics
        self.console.print("\n[bold]Detailed Statistics:[/bold]")
        successful_results = [r for r in self.results if r.error is None]
        if successful_results:
            total_tool_rec = sum(1 for r in successful_results if r.tool_recommended)
            total_correct = sum(1 for r in successful_results if r.correct_tool)
            total_params = sum(1 for r in successful_results if r.params_in_response)
            total_multistep = sum(1 for r in successful_results if r.multi_step_plan)
            
            self.console.print(f"  Total Tests: {len(self.results)}")
            self.console.print(f"  Tools Recommended: {total_tool_rec}/{len(successful_results)} ({total_tool_rec/len(successful_results)*100:.1f}%)")
            self.console.print(f"  Correct Tool Selection: {total_correct}/{len(successful_results)} ({total_correct/len(successful_results)*100:.1f}%)")
            self.console.print(f"  Parameters Extracted: {total_params}/{len(successful_results)} ({total_params/len(successful_results)*100:.1f}%)")
            self.console.print(f"  Multi-Step Plans: {total_multistep}/{len(successful_results)} ({total_multistep/len(successful_results)*100:.1f}%)")
            self.console.print(f"  Average TTFT: {sum(r.ttft for r in successful_results)/len(successful_results):.3f}s")
            self.console.print(f"  Average TPS: {sum(r.tps for r in successful_results)/len(successful_results):.2f}")
    
    def save_results(self, results: Optional[List[ToolBenchmarkResult]] = None):
        """Save results to JSON file."""
        if not results:
            results = self.results
        
        if not results:
            return
        
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tool_benchmark_results_{timestamp}.json"
        filepath = output_dir / filename
        
        data = {
            "config": {
                "model": self.config.model,
                "available_tools": len(AVAILABLE_TOOLS),
                "iterations": self.config.iterations,
            },
            "timestamp": datetime.now().isoformat(),
            "results": [
                {
                    "test_name": r.test_name,
                    "tool_type": r.tool_type,
                    "prompt_tokens": r.prompt_tokens,
                    "completion_tokens": r.completion_tokens,
                    "total_tokens": r.total_tokens,
                    "ttft": r.ttft,
                    "total_time": r.total_time,
                    "tps": r.tps,
                    "tool_recommended": r.tool_recommended,
                    "correct_tool": r.correct_tool,
                    "params_in_response": r.params_in_response,
                    "multi_step_plan": r.multi_step_plan,
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
    """Main entry point for the tool benchmark script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM Tool-Understanding Benchmark")
    parser.add_argument("--base-url", default="http://192.168.1.14:8080/v1",
                       help="Base URL of the LLM server")
    parser.add_argument("--api-key", default="no-key-required",
                       help="API key for the server")
    parser.add_argument("--model", default="Qwen3.5-35B-A3B-Q8_0",
                       help="Model name to benchmark")
    parser.add_argument("--iterations", type=int, default=3,
                       help="Number of iterations per test")
    parser.add_argument("--no-save", action="store_true",
                       help="Disable saving results to JSON")
    parser.add_argument("--output-dir", default="results",
                       help="Directory to save results")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Suppress verbose output")
    
    args = parser.parse_args()
    
    config = ToolBenchmarkConfig(
        base_url=args.base_url,
        api_key=args.api_key,
        model=args.model,
        iterations=args.iterations,
        save_json=not args.no_save,
        output_dir=args.output_dir,
        verbose=not args.quiet
    )
    
    benchmark = ToolBenchmark(config)
    results = await benchmark.run_benchmark()
    benchmark.display_results()
    
    if config.save_json and results:
        benchmark.save_results(results)


if __name__ == "__main__":
    asyncio.run(main())
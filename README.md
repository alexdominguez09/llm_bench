# LLM Benchmark

A comprehensive Python benchmarking tool for LLM inference servers. Measures performance metrics including tokens per second (TPS), time to first token (TTFT), and total response time for OpenAI-compatible APIs.

## Features

- **Performance Metrics**
  - Time to First Token (TTFT)
  - Tokens Per Second (TPS)
  - Total Response Time
  - Token count estimation

- **Benchmark Scenarios**
  - Short queries
  - Medium explanations
  - Long context understanding
  - Code generation
  - Mathematical reasoning
  - Creative writing

- **Multiple Output Sizes**
  - Configurable output token lengths (default: 100, 200, 500 tokens)

- **Streaming Support**
  - Benchmark both streaming and non-streaming modes

- **Results Export**
  - Console display with rich formatting
  - JSON export for further analysis

- **Tool Calling Benchmark** (Optional)
  - Tests LLM's understanding and planning for 69 tools across 7 categories
  - Web search, file system, GitHub, knowledge graph, documentation, browser automation, and utility tools

## Requirements

- Python 3.10+
- A running OpenAI-compatible LLM server (llama.cpp, Ollama, etc.)

## Installation

1. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```bash
# Run with default settings (connects to local llama.cpp server)
python benchmark.py

# Run with custom model
python benchmark.py --model "Qwen3.5-35B-A3B-Q8_0"

# Specify different output token counts
python benchmark.py --output-tokens 50 100 200

# Disable streaming mode
python benchmark.py --no-stream

# Increase iterations for more accurate results
python benchmark.py --iterations 5

# Run only tool calling benchmark
python benchmark.py --benchmark_type tool_call

# Run only speed benchmark
python benchmark.py --benchmark_type speed
```

### Command Line Options

```
usage: benchmark.py [-h] [--base-url BASE_URL] [--api-key API_KEY]
                    [--model MODEL] [--output-tokens OUTPUT_TOKENS [OUTPUT_TOKENS ...]]
                    [--iterations ITERATIONS] [--stream] [--no-stream]
                    [--timeout TIMEOUT] [--no-save] [--output-dir OUTPUT_DIR]
                    [--quiet] [--benchmark_type {speed,tool_call,all}]

options:
  -h, --help            show this help message and exit
  --base-url BASE_URL   Base URL of the LLM server (default: http://192.168.1.14:8080/v1)
  --api-key API_KEY     API key for the server (default: no-key-required)
  --model MODEL         Model name to benchmark (default: Qwen3.5-35B-A3B-Q8_0)
  --output-tokens       Number of output tokens to generate (default: 100 200 500)
  --iterations ITERATIONS
                        Number of iterations per test (default: 3)
  --stream              Enable streaming mode (default)
  --no-stream           Disable streaming mode
  --timeout TIMEOUT     Request timeout in seconds (default: 300.0)
  --no-save             Disable saving results to JSON
  --output-dir OUTPUT_DIR
                        Directory to save results (default: results)
  --quiet, -q           Suppress verbose output
  --benchmark_type {speed,tool_call,all}
                        Type of benchmark to run (default: all)
```

### Using a Configuration File

Create a `config.yaml` file:

```yaml
server:
  # Base URL of the OpenAI-compatible API server
  # For llama.cpp server: http://192.168.1.14:8080/v1
  # For Ollama: http://localhost:11434/v1
  # For Groq: https://api.groq.com/openai/v1
  base_url: "http://192.168.1.14:8080/v1"
  
  # API key (use "no-key-required" for local servers like llama.cpp)
  api_key: "no-key-required"
  
  # Model name to benchmark
  model: "Qwen3.5-35B-A3B-Q8_0"

benchmark:
  # Number of output tokens to generate for each test
  # Tests will run with these different output sizes
  output_tokens: [100, 200, 500]
  
  # Number of iterations per test (average results across iterations)
  iterations: 3
  
  # Test scenarios (prompts for different use cases)
  scenarios:
    - "short"      # Short queries (1-2 sentences)
    - "medium"     # Medium explanations
    - "long"       # Long context understanding
    - "coding"     # Code generation
    - "math"       # Mathematical reasoning
    - "creative"   # Creative writing
  
  # Prompt length variations (characters)
  prompt_lengths: [50, 200, 500]
  
  # Enable streaming mode (may affect timing)
  stream: true
  
  # Temperature for generation (0.0 - 1.0)
  temperature: 0.7
  
  # Top-p sampling (0.0 - 1.0)
  top_p: 0.9
  
  # Request timeout in seconds
  timeout: 300.0

output:
  # Directory to save JSON results
  output_dir: "results"
  
  # Save results to JSON file
  save_json: true
  
  # Verbose console output
  verbose: true
```

## Examples

### Benchmark Local llama.cpp Server

```bash
python benchmark.py \
  --base-url "http://192.168.1.14:8080/v1" \
  --model "Qwen3.5-35B-A3B-Q8_0" \
  --output-tokens 100 200 500 \
  --iterations 3
```

### Benchmark Ollama

```bash
python benchmark.py \
  --base-url "http://localhost:11434/v1" \
  --model "qwen2.5:7b"
```

### Benchmark Groq API

```bash
python benchmark.py \
  --base-url "https://api.groq.com/openai/v1" \
  --api-key "your-groq-api-key" \
  --model "llama3-70b-8192"
```

### Benchmark Together AI

```bash
python benchmark.py \
  --base-url "https://api.together.xyz/v1" \
  --api-key "your-together-api-key" \
  --model "Qwen/Qwen3.5-35B-A3B-Instruct-Turbo"
```

## Understanding Results

### Key Metrics

| Metric | Description |
|--------|-------------|
| **TTFT** | Time to First Token - Latency before first token appears |
| **TPS** | Tokens Per Second - Generation speed |
| **Total Time** | Complete response generation time |
| **Prompt Tokens** | Estimated input token count |
| **Completion Tokens** | Generated output token count |

### Typical Performance Ranges

| Hardware | TPS Range | TTFT Range |
|----------|-----------|------------|
| GPU (RTX 4090) | 30-80 t/s | 20-100ms |
| CPU (modern) | 3-15 t/s | 100-500ms |
| Cloud API | 20-100 t/s | 50-300ms |

## Output

### Console Output

```
┌─────────────────────────────────────────────────────────────┐
│                    Starting LLM Benchmark                    │
└─────────────────────────────────────────────────────────────┘
✓ Connected to server at http://192.168.1.14:8080/v1
Available models: Qwen3.5-35B-A3B-Q8_0, ...
✓ short_50chars_100tokens: 45.23 tps, TTFT: 0.032s, Time: 2.21s
✓ medium_200chars_200tokens: 42.15 tps, TTFT: 0.045s, Time: 4.75s
...

┌──────────────────────────────────────────────────────────────────────────────────────┐
│                            LLM Benchmark Results                                      │
├──────────┼──────────────┼─────────────┼───────────────────┼──────────────┼──────────┤
│ Test     │ Model        │ Prompt Tok. │ Completion Tok.   │ TTFT (s)   │ TPS      │
├──────────┼──────────────┼─────────────┼───────────────────┼──────────────┼──────────┤
│ short_50 │ Qwen3.5-35B  │ 13          │ 100               │ 0.032        │ 45.23    │
├──────────┼──────────────┼─────────────┼───────────────────┼──────────────┼──────────┤
│ medium_200│ Qwen3.5-35B │ 50          │ 200               │ 0.045        │ 42.15    │
└──────────┴──────────────┴─────────────┴───────────────────┴──────────────┴──────────┘

Summary Statistics:
  Average Tokens/Second: 43.56
  Average TTFT: 0.038s
  Average Total Time: 3.48s
  Total Tests Run: 54
  Successful Tests: 54

✓ Results saved to results/benchmark_results_20260318_014512.json
```

### JSON Output

Results are saved in `results/` directory as JSON files:

```json
{
  "config": {
    "base_url": "http://192.168.1.14:8080/v1",
    "model": "Qwen3.5-35B-A3B-Q8_0"
  },
  "timestamp": "2026-03-18T01:45:12.345678",
  "results": [
    {
      "test_name": "short_50chars_100tokens",
      "model": "Qwen3.5-35B-A3B-Q8_0",
      "prompt_tokens": 13,
      "completion_tokens": 100,
      "total_tokens": 113,
      "ttft": 0.032,
      "total_time": 2.21,
      "tps": 45.23,
      "stream": true
    }
  ]
}
```

## Troubleshooting

### Connection Issues

```
✗ Connection failed: Connection refused
```

**Solution**: Ensure the llama.cpp server is running:
```bash
./llama-server -m model.gguf -c 4096 -t 8 --port 8080
```

### Model Not Found

```
Server error: 404 - {"error": "Model not found"}
```

**Solution**: Check the model name matches what's loaded on the server. List available models:
```bash
curl http://192.168.1.14:8080/v1/models
```

### Timeout Errors

```
Error: Request timed out
```

**Solution**: Increase timeout for longer generations:
```bash
python benchmark.py --timeout 600
```

## License

MIT License
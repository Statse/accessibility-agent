# Ollama Integration Guide

This guide explains how to use Ollama for local LLM inference with the Accessibility Agent, providing a private, cost-free alternative to cloud-based LLM APIs.

## Table of Contents

- [What is Ollama?](#what-is-ollama)
- [Benefits of Using Ollama](#benefits-of-using-ollama)
- [Installation](#installation)
- [Configuration](#configuration)
- [Recommended Models](#recommended-models)
- [Usage](#usage)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Performance Considerations](#performance-considerations)

## What is Ollama?

[Ollama](https://ollama.com) is a tool that makes it easy to run large language models (LLMs) locally on your computer. It provides an OpenAI-compatible API, making integration straightforward.

## Benefits of Using Ollama

- **Privacy**: Keep accessibility testing data completely local
- **Cost Efficiency**: No API costs for LLM inference
- **Offline Capability**: Run tests without internet connection
- **Customization**: Use fine-tuned or specialized models
- **Speed**: Local inference can be faster than API calls (depending on hardware)

## Installation

### Step 1: Install Ollama

**Windows:**
1. Download the installer from [ollama.com](https://ollama.com/download)
2. Run the installer
3. Ollama will be available from the command line

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2: Start Ollama Server

```bash
ollama serve
```

The server will start on `http://localhost:11434` by default.

**Note:** On Windows, Ollama typically runs as a background service automatically after installation.

### Step 3: Pull a Model

Download a model to use with the accessibility agent:

```bash
# Recommended: Llama 3.2 (3B parameters, fast and capable)
ollama pull llama3.2

# Alternative: Mistral (7B parameters, more capable but slower)
ollama pull mistral

# Alternative: Qwen 2.5 (7B parameters, good reasoning)
ollama pull qwen2.5
```

## Configuration

### Option 1: Environment Variables (Recommended)

Create or update your `.env` file:

```bash
# Set Ollama as the LLM provider
LLM_PROVIDER=ollama

# Set the model to use
LLM_MODEL=llama3.2

# Optional: Set custom Ollama server URL
# OLLAMA_BASE_URL=http://localhost:11434
```

### Option 2: Configuration File

Edit `config/settings.yaml`:

```yaml
agent:
  # Set provider to ollama
  provider: "ollama"

  # Set model (without "ollama:" prefix in settings.yaml)
  model: "llama3.2"

  # Ollama server settings
  ollama:
    base_url: "http://localhost:11434/v1"
    default_model: "llama3.2"
    timeout: 120.0
```

### Option 3: Programmatic Configuration

When initializing the `AccessibilityAgent` directly:

```python
from src.agent.accessibility_agent import AccessibilityAgent

agent = AccessibilityAgent(
    model="llama3.2",
    provider="ollama",
    ollama_base_url="http://localhost:11434/v1"
)
```

## Recommended Models

### For Best Performance (if you have a good GPU)

- **llama3.2** (3B parameters)
  - Fast inference
  - Good for accessibility testing tasks
  - Requires ~2GB VRAM
  - `ollama pull llama3.2`

- **mistral** (7B parameters)
  - More capable reasoning
  - Better at complex accessibility analysis
  - Requires ~4-5GB VRAM
  - `ollama pull mistral`

### For CPU-only Systems

- **llama3.2** (3B parameters)
  - Still performant on CPU
  - ~10-20 seconds per inference on modern CPUs

- **phi3** (3.8B parameters)
  - Optimized for efficiency
  - Fast on CPU
  - `ollama pull phi3`

### For Maximum Capability (if you have powerful hardware)

- **qwen2.5** (14B parameters)
  - Excellent reasoning capabilities
  - Great for complex accessibility patterns
  - Requires ~8-10GB VRAM
  - `ollama pull qwen2.5:14b`

## Usage

### Running the Accessibility Agent with Ollama

Once configured, use the agent normally:

```bash
# Using environment variables from .env
python -m src.main https://example.com

# Or override settings via CLI (if implemented)
python -m src.main https://example.com --provider ollama --model llama3.2
```

### Switching Between Providers

You can easily switch between Ollama and OpenAI:

**Use Ollama (local):**
```bash
# In .env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
```

**Use OpenAI (cloud):**
```bash
# In .env
LLM_PROVIDER=openai
LLM_MODEL=openai:gpt-4
OPENAI_API_KEY=sk-your-api-key
```

## Testing

### Verify Ollama Integration

Run the included test script:

```bash
python test_ollama.py
```

This will verify:
1. Ollama server is running
2. Models are available
3. AccessibilityAgent can initialize with Ollama
4. Configuration is loaded correctly

### Expected Output

```
======================================================================
               OLLAMA INTEGRATION TEST SUITE
======================================================================

============================================================
TEST 1: Ollama Server Connection
============================================================
✓ Ollama server is running
✓ Available models: 2
  - llama3.2:latest
  - mistral:latest

============================================================
TEST 2: AccessibilityAgent with Ollama
============================================================
✓ AccessibilityAgent initialized with Ollama
✓ Agent instance created: AccessibilityAgent
✓ Pydantic AI agent created: Agent

✅ ALL TESTS PASSED
```

## Troubleshooting

### Issue: "Cannot connect to Ollama server"

**Solution:**
1. Check if Ollama is running: `ollama list`
2. Start the server: `ollama serve`
3. Verify the port is correct (default: 11434)

### Issue: "Model not found"

**Solution:**
1. List available models: `ollama list`
2. Pull the required model: `ollama pull llama3.2`
3. Update your configuration to use an available model

### Issue: "Inference is too slow"

**Solutions:**
1. Use a smaller model (e.g., `llama3.2` instead of `mistral`)
2. Close other applications to free up RAM/VRAM
3. Enable GPU acceleration if available
4. Reduce the `max_actions` setting in `config/settings.yaml`

### Issue: "Out of memory"

**Solutions:**
1. Use a smaller model
2. Close other applications
3. For Windows: Increase virtual memory/page file size
4. Consider using quantized models (Ollama uses quantized versions by default)

### Issue: "Model responses are not good enough"

**Solutions:**
1. Use a larger model (e.g., `mistral` or `qwen2.5:14b`)
2. Adjust the `temperature` setting in `config/settings.yaml` (try 0.3-0.5 for more deterministic responses)
3. Consider using OpenAI for complex pages and Ollama for simpler ones

## Performance Considerations

### Hardware Requirements

| Model Size | CPU RAM | GPU VRAM | CPU Speed (approx) | GPU Speed (approx) |
|-----------|---------|----------|-------------------|-------------------|
| 3B params | 4GB     | 2GB      | 10-20s per call   | 1-3s per call     |
| 7B params | 8GB     | 4-5GB    | 30-60s per call   | 2-5s per call     |
| 14B params| 16GB    | 8-10GB   | 60-120s per call  | 5-10s per call    |

### Optimization Tips

1. **Use GPU acceleration** if available (Ollama automatically uses NVIDIA GPUs)
2. **Keep the model loaded** by making a dummy request before running tests
3. **Reduce max_actions** to limit the number of LLM calls
4. **Use smaller models** for simpler accessibility tests
5. **Batch testing** - test multiple pages in one session to amortize model loading time

### Comparing Ollama vs OpenAI

| Feature | Ollama (Local) | OpenAI (Cloud) |
|---------|---------------|----------------|
| **Privacy** | Complete | Data sent to OpenAI |
| **Cost** | Free (hardware cost) | Pay per token |
| **Speed** | Depends on hardware | Fast (2-5s typical) |
| **Quality** | Good (model-dependent) | Excellent (GPT-4) |
| **Internet** | Not required | Required |
| **Setup** | Model download required | API key required |

## Advanced Configuration

### Using a Remote Ollama Server

If you have Ollama running on a different machine:

```bash
# In .env
OLLAMA_BASE_URL=http://192.168.1.100:11434
```

### Using Ollama Cloud

Ollama also offers a cloud service:

```bash
# In .env
OLLAMA_BASE_URL=https://ollama.com/v1
OLLAMA_API_KEY=your-api-key
```

### Custom Model Parameters

When running Ollama, you can customize model parameters:

```bash
# Create a Modelfile
ollama create accessibility-llama -f Modelfile
```

Example `Modelfile`:
```
FROM llama3.2

PARAMETER temperature 0.5
PARAMETER top_p 0.9
PARAMETER num_ctx 4096

SYSTEM You are an accessibility testing expert who analyzes web pages for WCAG compliance issues.
```

Then use the custom model:
```bash
# In .env
LLM_MODEL=accessibility-llama
```

## Next Steps

1. Install and start Ollama: `ollama serve`
2. Pull a recommended model: `ollama pull llama3.2`
3. Configure your `.env` file with `LLM_PROVIDER=ollama`
4. Run the test script: `python test_ollama.py`
5. Start testing websites: `python -m src.main https://example.com`

## Resources

- [Ollama Official Website](https://ollama.com)
- [Ollama Model Library](https://ollama.com/library)
- [Ollama GitHub Repository](https://github.com/ollama/ollama)
- [Pydantic AI Documentation](https://ai.pydantic.dev/)
- [Accessibility Agent README](../README.md)

# ForgeAgent Development Guide

## Testing

Run the test suite using Python's standard `unittest` framework:

```bash
# Discover and run all unit and integration tests
python3 -m unittest discover tests

# Run specific test modules
python3 -m unittest tests/unit/test_config.py
python3 -m unittest tests/unit/test_git_engine.py
python3 -m unittest tests/unit/test_tools.py
python3 -m unittest tests/unit/test_orchestrator.py
```

## Running Benchmarks

```bash
# Execute benchmark levels 1 through 7
python3 benchmarks/runner.py
```

## Adding New Agents or Tools

1. **New Tools**: Inherit from `forgeagent.tools.base.BaseTool`, implement `_run()`, and register in `ToolRegistry._register_default_tools()`.
2. **New Agents**: Inherit from `forgeagent.agents.base.BaseAgent` and implement `run(state, **kwargs)`.
3. **New LLM Providers**: Inherit from `forgeagent.llm.base.LLMProvider`, implement `generate()` and `generate_structured()`, and add to `forgeagent.llm.factory.get_llm_provider()`.

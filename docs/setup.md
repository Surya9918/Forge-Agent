# Setup & Installation Guide for ForgeAgent

## Prerequisites
- Python 3.9 or higher
- Git 2.30+
- (Optional) Docker for containerized sandboxing
- Google Antigravity 2.0, Antigravity IDE, or Antigravity CLI

## Quick Installation

```bash
# Clone the repository
git clone https://github.com/your-org/forgeagent.git
cd forgeagent

# Install package locally
pip install -e .
```

## Configuring Antigravity MCP Integration

To connect ForgeAgent to Google Antigravity as an active MCP server:

1. Open your workspace and create or edit `.agents/mcp_config.json`:
```json
{
  "mcpServers": {
    "forgeagent": {
      "command": "forge",
      "args": ["mcp"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

2. Alternatively, configure globally in `~/.gemini/config/mcp_config.json`.

3. In Antigravity CLI, run `/mcp` to verify the connection status ring turns green. In Antigravity IDE, open the Agent Side Panel, select **MCP Servers**, and verify `forgeagent` is listed.

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key | (Optional in mock mode) |
| `OPENAI_API_KEY` | OpenAI API key | (Optional) |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | (Optional) |
| `GITHUB_TOKEN` | GitHub Personal Access Token or App Token | (Optional / Mock simulation active) |
| `FORGE_MODE` | Autonomy mode override (`assisted`, `autonomous`, `safe_production`) | `autonomous` |
| `FORGE_LLM_PROVIDER` | LLM provider override (`google`, `openai`, `anthropic`, `ollama`, `mock`) | `mock` |

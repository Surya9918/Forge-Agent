# ForgeAgent

> **Autonomous Software Engineering inside Antigravity**

[![Antigravity Compatible](https://img.shields.io/badge/Antigravity-2.0%20%7C%20IDE%20%7C%20CLI-blue)](https://antigravity.google)
[![MCP Compliant](https://img.shields.io/badge/MCP-2024--11--05-green)](https://modelcontextprotocol.io)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](LICENSE)

ForgeAgent is a production-ready autonomous software engineering system and Model Context Protocol (MCP) server purpose-built for **Google Antigravity**.

Instead of acting merely as a conversational chatbot, ForgeAgent functions as a full-lifecycle autonomous software engineer: it ingests high-level software requirements, devises implementation plans and architecture specs, initializes repositories, implements clean modular code, executes builds, analyzes test failures, performs automated self-healing, manages Git version control, interacts with GitHub, and repairs CI pipeline failures.

---

## Architecture Overview

ForgeAgent implements a **Tri-Tier Hybrid Integration Architecture** designed around Google Antigravity's real platform primitives:

1. **Native MCP Server (`forgeagent.antigravity.mcp_server`)**:
   Standard Model Context Protocol (MCP) JSON-RPC 2.0 interface exposing autonomous engineering tools (`forge_plan`, `forge_develop`, `forge_test_and_heal`, `forge_status`, `forge_git_commit`, `forge_github_pr`) over `stdio` and HTTP/SSE. Registered directly in `.agents/mcp_config.json`.
2. **Antigravity Verifiable Artifacts Engine (`forgeagent.antigravity.artifacts`)**:
   Emits verifiable structured artifacts (`implementation_plan.md`, `walkthrough.md`, `verification_report.md`, `code_review.md`) directly into `.agents/artifacts/` for native rendering in Antigravity's Manager view and terminal review overlays.
3. **Autonomous CLI Companion (`forge`)**:
   A terminal-first executive CLI with real-time TUI progress bars, multi-agent coordination, and configurable human-in-the-loop approvals.

---

## Key Features

- **Multi-Agent Orchestration**: Specialized subagents (Planner, Architect, Coder, Tester, Debugger, Reviewer, Security Officer).
- **Self-Healing Loop**: Autonomous build/test execution, error localization, repair generation, and regression verification with configurable iteration bounds.
- **Three Autonomy Modes**:
  - `assisted`: Human approves plans, code modifications, and git operations.
  - `autonomous`: Agent acts autonomously within workspace boundaries.
  - `safe_production`: Disallows force-pushes, protected branch modifications, and unreviewed production merges.
- **Robust Git & GitHub Integration**: Automated branch creation, conventional commit formatting, pull request generation, and CI status tracking.
- **CI Self-Healing**: Automated generation of GitHub Actions workflows (`.github/workflows/ci.yml`), log diagnosis, and automated repair commits.
- **Hermetic Security & Zero-Secret Leakage**: Automatic regex masking of tokens, workspace path confinement, and command policy engines.
- **Model Independence**: Swappable LLM adapters for Google Gemini, OpenAI, Anthropic Claude, Ollama, and an offline Mock provider.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/forgeagent.git
cd forgeagent

# Install with pip (local editable mode)
pip install -e .
```

---

## Antigravity IDE & CLI Configuration

ForgeAgent connects natively to Google Antigravity via MCP. The recommended approach is to install it as an **Antigravity Plugin**.

Create a directory at `~/.gemini/config/plugins/forgeagent/` (for global use) or `.agents/plugins/forgeagent/` (for workspace use), and add the following two files:

**1. `plugin.json` (Manifest)**
```json
{
  "name": "forgeagent"
}
```

**2. `mcp_config.json` (MCP Server config)**
```json
{
  "mcpServers": {
    "forgeagent": {
      "command": "python",
      "args": ["-m", "forgeagent.antigravity.mcp_server"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```
*(Note: Use `"python"` for Windows or `"python3"` for Linux/macOS as appropriate for your environment)*

Once configured, Antigravity IDE and CLI will automatically discover the plugin and can autonomously invoke `forge_develop`, `forge_plan`, and `forge_test_and_heal`.

---

## Configuration (`forge.yaml`)

```yaml
project:
  name: "my-project"
  workspace: "./workspace"

agent:
  mode: "autonomous"      # assisted | autonomous | safe_production
  max_iterations: 10     # Max self-healing attempts
  max_runtime_minutes: 120

llm:
  provider: "google"      # google | openai | anthropic | ollama | mock
  model: "gemini-2.0-flash"
  api_key_env: "GEMINI_API_KEY"

git:
  auto_commit: true
  auto_push: true
  default_branch: "main"
  protected_branches:
    - "main"
    - "master"
    - "production"

github:
  enabled: true
  token_env: "GITHUB_TOKEN"
  create_repository: true
  create_pull_request: true

security:
  require_approval_for:
    - "repository_delete"
    - "force_push"
    - "production_deploy"
```

---

## CLI Usage

```bash
# 1. Create a project and let ForgeAgent develop it autonomously
forge create "Build a task management application with React and Node.js" --name task-manager

# 2. Check active task progress, test metrics, and git status
forge status

# 3. Pause or resume autonomous execution
forge pause
forge resume

# 4. Approve pending actions when running in Assisted Mode
forge approve

# 5. Start the MCP server for Antigravity integration
forge mcp
```

---

## Security & Isolation

ForgeAgent implements defense-in-depth:
- **Sandbox Manager**: Executes untrusted or generated code within Docker containers or scrubbed subprocesses with strict execution timeouts.
- **Zero-Secret Disclosure**: Prompts and logs are dynamically scrubbed of API keys, GitHub tokens, and private SSH certificates.
- **Workspace Confinement**: Resolves all file paths against the project root, denying path traversal attempts (`../`).
- See [docs/security/threat-model.md](docs/security/threat-model.md) for the complete threat model and mitigation matrix.

---

## Development & Testing

```bash
# Run unit, integration, and sandbox test suites
python3 -m unittest discover tests

# Run benchmark evaluations (Levels 1 to 7)
python3 benchmarks/runner.py
```

---

## License

Licensed under the Apache License, Version 2.0.

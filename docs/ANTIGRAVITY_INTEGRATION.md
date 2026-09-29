# Google Antigravity Platform Integration Analysis & Architecture Decision Record (ADR)

**Product:** ForgeAgent — Autonomous Software Engineering inside Antigravity  
**Author:** Software Architect & AI Agent Systems Team  
**Status:** Approved & Implemented  
**Date:** September 2026  

---

## 1. Executive Summary

Google Antigravity is an agent-first development platform released by Google encompassing **Antigravity 2.0**, **Antigravity IDE** (featuring dual-view Editor and Manager interfaces), **Antigravity CLI** (`agy`), and the **Antigravity SDK** (`google-antigravity` in Python). Rather than requiring developers to manually parse raw chat logs, Antigravity introduces verifiable **Artifacts** (Implementation Plans, Code Diffs, Walkthroughs, Screenshots, and Verification Reports) for asynchronous human-in-the-loop review and multi-agent orchestration.

This document records the architectural research into Antigravity's real-world extension points, APIs, protocols, and security boundaries. Based on official Antigravity platform capabilities, we define the integration architecture for **ForgeAgent**.

---

## 2. Real Antigravity Platform Capabilities Analysis

### 2.1 Official Extension & Integration Mechanisms

Based on official platform documentation (`antigravity.google/docs/mcp/`, `antigravity.google/docs/sdk/overview/`, and `antigravity.google/docs/artifacts/`):

1. **Model Context Protocol (MCP)**:
   - **Support**: Native, first-class across Antigravity 2.0, Antigravity IDE, Antigravity CLI, and the Python SDK.
   - **Configuration Files**:
     - Global: `~/.gemini/config/mcp_config.json`
     - Workspace-local: `<workspace>/.agents/mcp_config.json`
   - **Supported Transports**:
     - `stdio`: Executable invocation via standard I/O pipes (`command`, `args`, `env`, `cwd`).
     - `serverUrl`: Remote Streamable HTTP / SSE / WebSocket transport.
   - **Authentication**:
     - Google Application Default Credentials (`authProviderType: "google_credentials"`).
     - OAuth 2.0 with Dynamic Client Registration (DCR) or client credentials with redirect `https://antigravity.google/oauth-callback`.
     - Custom HTTP headers (bearer tokens, API keys).
   - **Permissions System**:
     - Antigravity enforces access control: `mcp(server/tool)`, `mcp(server/*)`, `mcp(*)`.
     - Default mode is `Ask` mode (human approval required before execution).

2. **Antigravity SDK (`google-antigravity`)**:
   - Python-native framework managing binary discovery, tool execution, session lifecycles, and subagents.
   - Key abstractions:
     - `Agent`: Core runner behind an async context manager (`async with Agent(config) as agent:`).
     - `LocalAgentConfig`: Supports Vertex AI / Gemini Enterprise credentials, local models (LiteRT, local OpenAI-compatible endpoints), custom personas, and system instructions.
     - Custom Tools: Python function registration with typed schemas.
     - Policies: Declarative access control (`allow`, `ask`, `deny`).
     - Subagents: Dynamic multi-agent delegation and role-based execution.
     - Lifecycle Hooks & Triggers: Background event triggers and persistence.

3. **Antigravity Verifiable Artifacts System**:
   - Asynchronous collaboration primitive: instead of streaming raw tool spam into user chat, agents produce structured artifacts reviewed in:
     - **Antigravity IDE**: Visual sidebar & review pane with interactive approval, visual code diffs, and walkthroughs.
     - **Antigravity CLI**: Terminal keyboard-driven review panel and status bar notifications.
   - Standard artifact types:
     - `Implementation Plan` (`plan.md`): Phased decomposition, task breakdown, acceptance criteria.
     - `Code Diffs & Walkthrough` (`walkthrough.md`): Changes explained with rationale.
     - `Verification Results` (`verification.md`): Test passes/failures, build outputs, CI statuses.

4. **External Process & Terminal Execution**:
   - Antigravity supports sandbox isolation for command execution.
   - Workspace boundaries must be strictly enforced.
   - Destructive operations (`rm -rf /`, format disks, credential leakage) must be trapped by security policy engines.

5. **Packaging and Distribution**:
   - Standard Python package (`pip install forgeagent` / `wheel`).
   - Standard MCP server declaration inside `.agents/mcp_config.json`.
   - Standalone CLI companion (`forge`).

---

## 3. Architecture Evaluation & Selection

We evaluated six architectural alternatives:

| Alternative | Feasibility | Ecosystem Fit | Pros | Cons |
|---|---|---|---|---|
| **A. Pure VS Code Extension** | Low | Narrow | Good for VS Code only | Does not work with Antigravity CLI or standalone Antigravity 2.0 runtime |
| **B. Proprietary Antigravity Plugin** | Infeasible | None | N/A | Antigravity uses open standards (MCP, Skills, SDK) rather than closed plugin formats |
| **C. Standard MCP Server** | High | Universal | Natively supported by Antigravity 2.0, IDE, and CLI; zero API fabrication | Requires separate process or transport; tool call granularity |
| **D. Standalone CLI Companion** | High | High | Works anywhere, easy terminal scripting, headless CI mode | Requires user to leave IDE unless called from terminal |
| **E. Antigravity SDK Agent Extension** | High | Deep | Native Python async hooks, subagents, and memory | Requires Python environment |
| **F. Tri-Tier Hybrid Architecture (Selected)** | **Highest** | **Complete** | **Combines MCP server + Antigravity SDK & Artifacts bridge + Full CLI companion** | Requires clean modular design |

### Decision: Architecture F — The Tri-Tier Hybrid Architecture

ForgeAgent adopts a **Tri-Tier Modular Architecture**:

1. **Tier 1: Native Antigravity MCP Server (`forgeagent.mcp`)**:
   - Implements standard Model Context Protocol (v1.0 compliant) over `stdio` and Streamable HTTP.
   - Registered seamlessly in `.agents/mcp_config.json` and `~/.gemini/config/mcp_config.json`.
   - Exposes high-level autonomous engineering tools (`forge_plan`, `forge_develop`, `forge_test_and_heal`, `forge_git_commit`, `forge_github_pr`, `forge_ci_heal`, `forge_status`).

2. **Tier 2: Antigravity Artifacts & SDK Engine (`forgeagent.engine`)**:
   - Emits native Antigravity Artifacts:
     - `.agents/artifacts/implementation_plan.md`
     - `.agents/artifacts/walkthrough.md`
     - `.agents/artifacts/verification_report.md`
     - `.agents/artifacts/code_review.md`
   - Integrates with Antigravity's dual-view Manager and Editor panels.
   - Provides specialized subagents: Planner, Architect, Coder, Tester, Debugger, Reviewer, and Security Officer.

3. **Tier 3: Autonomous CLI Companion (`forge`)**:
   - Fully scriptable CLI executable: `forge create`, `forge run`, `forge status`, `forge approve`, `forge heal`, `forge github`.
   - Embedded TUI dashboard showing real-time progress, test results, Git status, and CI runs.
   - Headless daemon and CI runner mode.

---

## 4. Communication & Protocol Flow

```text
       ┌────────────────────────────────────────────────────────┐
       │                Google Antigravity Surfaces             │
       │  (Antigravity 2.0  /  Antigravity IDE  /  AGY CLI)     │
       └──────────────┬──────────────────────────┬──────────────┘
                      │                          │
        MCP (stdio / SSE / HTTP)     Artifact File Watcher
                      │                          │
                      ▼                          ▼
       ┌────────────────────────────────────────────────────────┐
       │             ForgeAgent Antigravity Bridge              │
       │                                                        │
       │  ┌────────────────────────┐  ┌──────────────────────┐  │
       │  │    MCP Server Tier     │  │   Artifact Manager   │  │
       │  │ (Tools, Prompts, Res)  │  │ (.agents/artifacts/) │  │
       │  └───────────┬────────────┘  └──────────▲───────────┘  │
       └──────────────┼──────────────────────────┼──────────────┘
                      │                          │
                      ▼                          │
       ┌─────────────────────────────────────────┴──────────────┐
       │                 ForgeAgent Core Engine                 │
       │                                                        │
       │   [Agent Orchestrator] ──► [Planner / Architect]      │
       │            │           ──► [Coder / Reviewer]          │
       │            │           ──► [Tester / Debugger]         │
       │            ▼                                           │
       │   [Self-Healing Loop]  ◄── [Repository Intelligence]   │
       │            │                                           │
       │   ┌────────┴─────────┬───────────────────┐             │
       │   ▼                  ▼                   ▼             │
       │ [Tool Layer]    [Sandbox Runner]   [Git / GitHub Engine│
       │ (Security-gated) (Docker / Process) (CI Polling & Heal)│
       └────────────────────────────────────────────────────────┘
```

---

## 5. Security, Permissions & Credentials

1. **Workspace Boundary Enforcement**:
   - Commands and filesystem writes are strictly confined to the project root unless explicitly permitted.
   - Path traversal prevention (`..` canonical path checks).

2. **Zero-Secret Disclosure Protocol**:
   - The LLM context never sees raw API keys, GitHub tokens, or private SSH keys.
   - Dynamic secret masking: regex scrubber for `ghp_`, `github_pat_`, `sk-`, `AWS_`, `BEGIN PRIVATE KEY`.

3. **Command Policy Engine**:
   - Tiered execution: Safe Commands (allowlist), Supervised Commands (requires approval in Assisted mode), Denied Commands (hard block on `rm -rf /`, `dd`, `mkfs`, fork bombs).

4. **Autonomy Guardrails**:
   - Configurable limits on iterations (`max_iterations: 10`), runtime, changed files, and token budgets.
   - Automatic escalation to human when confidence is low or loop limit is reached.

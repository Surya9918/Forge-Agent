# ForgeAgent: System Architecture & Technical Specification

**Product:** ForgeAgent  
**Tagline:** Autonomous Software Engineering inside Antigravity.  
**Version:** 0.1.0  
**Status:** Implemented & Verified  

---

## 1. Executive Summary

ForgeAgent is an autonomous software engineering engine and integration plugin designed natively for **Google Antigravity** (including Antigravity 2.0, Antigravity IDE, Antigravity CLI, and the Antigravity Python SDK). Unlike conversational chatbots that merely output static code snippets, ForgeAgent operates as an autonomous engineering orchestrator that takes high-level user specifications and executes the full engineering lifecycle:
- Requirement decomposition & phased planning
- Architectural design & API contracts
- Project scaffolding & code generation
- Multi-language test discovery & execution
- Autonomous self-healing test/fix cycles
- Git version control & conventional commit creation
- GitHub repository provisioning, branch pushing, and pull request opening
- CI/CD workflow generation and remote CI self-healing
- Verifiable Antigravity Artifact production

---

## 2. System Architecture & Component Diagram

```text
                     +---------------------------------------+
                     |       Google Antigravity Platform     |
                     | (Antigravity 2.0 / IDE / CLI / SDK)   |
                     +-------------------+-------------------+
                                         |
                       +-----------------+-----------------+
                       |                                   |
         MCP Protocol (stdio/HTTP)             File Watcher / Artifacts
                       |                                   |
                       v                                   v
         +-----------------------------+     +-----------------------------+
         |    ForgeMCPServer (MCP)     |     | Antigravity Artifact Engine |
         | (tools/call, tools/list,    |     | (.agents/artifacts/*.md)    |
         |  resources/read, prompts)   |     +-----------------------------+
         +--------------+--------------+                   ^
                        |                                  |
                        +----------------+-----------------+
                                         |
                                         v
         +-----------------------------------------------------------------+
         |                    Agent Orchestrator                           |
         |  - State Manager (.forge/state/task_id.json)                    |
         |  - Event Bus (PROJECT_CREATED, TASK_STARTED, FIX_APPLIED, etc.) |
         |  - Autonomy Policy Gate (assisted, autonomous, safe_production) |
         +-------+---------------+---------------+---------------+---------+
                 |               |               |               |
                 v               v               v               v
           +-----------+   +-----------+   +-----------+   +-----------+
           |  Planner  |   | Architect |   |   Coder   |   |  Reviewer |
           |   Agent   |   |   Agent   |   |   Agent   |   |   Agent   |
           +-----+-----+   +-----+-----+   +-----+-----+   +-----+-----+
                 |               |               |               |
                 +---------------+---------------+---------------+
                                         |
                                         v
         +-----------------------------------------------------------------+
         |                 Self-Healing Verification Loop                  |
         |                                                                 |
         |      [Coder] ---> [Tester (Auto-Detect)] ---> Pass?             |
         |                      |                         /    \           |
         |                      v                       Yes     No         |
         |              [Failure Locator]                |       |         |
         |                      v                        v       v         |
         |              [Debugger Agent] <----------- Continue  [Heal]     |
         +-------------------------------+---------------------------------+
                                         |
                        +----------------+----------------+
                        |                                 |
                        v                                 v
         +-----------------------------+   +-------------------------------+
         |    Security & Sandbox Layer |   |   Git & GitHub Engine         |
         | - Path boundary enforcement |   | - Git CLI abstraction         |
         | - Process isolation / Docker|   | - Conventional commits        |
         | - Secret scrubbing/redactor |   | - GitHub App / Token auth     |
         | - Command allow/denylists   |   | - PR & CI log self-healer     |
         +-----------------------------+   +-------------------------------+
```

---

## 3. Directory Structure

```text
forgeagent/
├── __init__.py                # Package version, exports, metadata
├── config/
│   ├── __init__.py
│   ├── models.py              # Pydantic configuration schemas & autonomy modes
│   └── loader.py              # YAML/JSON loader, env overrides, validation
├── llm/
│   ├── __init__.py
│   ├── base.py                # LLMProvider base class, ChatMessage, LLMResponse
│   ├── factory.py             # LLM provider factory
│   ├── google_provider.py     # Google Gemini API adapter
│   ├── openai_provider.py     # OpenAI API adapter
│   ├── anthropic_provider.py  # Anthropic Claude adapter
│   ├── ollama_provider.py     # Ollama local model adapter
│   └── mock_provider.py       # Deterministic mock provider for hermetic testing
├── sandbox/
│   ├── __init__.py
│   ├── base.py                # SandboxRunner base class & CommandResult
│   ├── local_sandbox.py       # LocalProcessSandbox with timeout & boundaries
│   ├── docker_sandbox.py      # Docker containerized execution
│   └── manager.py             # SandboxManager lifecycle coordinator
├── tools/
│   ├── __init__.py
│   ├── base.py                # BaseTool & ToolResult with permission gates
│   ├── filesystem.py          # Read, write, edit, delete, list, search
│   ├── terminal.py            # run_command, run_tests, run_build, inspect
│   └── registry.py            # Central registry for all tools
├── git/
│   ├── __init__.py
│   ├── engine.py              # Git CLI engine (init, diff, log, commit, branch)
│   └── tools.py               # Tool wrappers for agent invocation
├── github/
│   ├── __init__.py
│   ├── client.py              # REST API client & simulated in-memory store
│   └── tools.py               # github_create_repository, create_pr, etc.
├── intelligence/
│   ├── __init__.py
│   ├── detector.py            # Multi-language stack & test framework detector
│   └── analyzer.py            # AST/symbol indexer, TODO scanner, snippets
├── ci/
│   ├── __init__.py
│   ├── generator.py           # GitHub Actions workflow generator
│   └── healer.py              # Remote CI log analyzer & auto-repair loop
├── state/
│   ├── __init__.py
│   ├── state.py               # TaskState, TestSummary, AgentPhase
│   └── persistence.py         # JSON state persistence & crash recovery
├── events/
│   ├── __init__.py
│   ├── events.py              # ForgeEvent & EventType enumerations
│   └── bus.py                 # Publish-subscribe central event bus
├── observability/
│   ├── __init__.py
│   ├── redactor.py            # Regex secret masking (ghp, sk, private keys)
│   └── logger.py              # JSON structured file logging
├── agents/
│   ├── __init__.py
│   ├── base.py                # BaseAgent abstraction
│   ├── planner.py             # Requirement analysis & task decomposition
│   ├── architect.py           # Architecture & technical spec authoring
│   ├── coder.py               # Incremental task implementation
│   ├── tester.py              # Build & test execution & metric parser
│   ├── debugger.py            # Error localization & self-healing patcher
│   ├── reviewer.py            # Quality, security, & maintainability reviewer
│   └── orchestrator.py        # Central multi-agent coordinator
├── antigravity/
│   ├── __init__.py
│   ├── mcp_server.py          # MCP JSON-RPC 2.0 server (stdio & HTTP)
│   ├── artifacts.py           # Antigravity Verifiable Artifacts generator
│   └── sdk_bridge.py          # Python SDK bridge for google-antigravity
└── cli/
    ├── __init__.py
    └── main.py                # Click CLI companion with Rich TUI
```

---

## 4. Multi-Agent Orchestration & Data Contracts

Each agent operates on structured Pydantic models:

1. **Planner Agent (`DevelopmentPlan`)**:
   ```json
   {
     "project": "task-manager",
     "description": "Full-stack task application",
     "stack": {"frontend": "React", "backend": "Node.js", "database": "PostgreSQL"},
     "tasks": [
       {"id": "task-1", "title": "Setup project", "target_files": ["package.json"], "dependencies": []}
     ],
     "acceptance_criteria": ["Project builds", "Tests pass"]
   }
   ```

2. **Coder Agent (`TaskImplementation`)**:
   ```json
   {
     "task_id": "task-1",
     "actions": [
       {"file_path": "server.js", "action": "write", "content": "...", "explanation": "Express server"}
     ],
     "notes": "Implemented server entrypoint"
   }
   ```

3. **Debugger Agent (`RepairPatch`)**:
   ```json
   {
     "analysis": "Syntax error in routes/auth.js: missing closing brace",
     "file_path": "routes/auth.js",
     "fixed_content": "...",
     "explanation": "Added missing brace and validated export",
     "confidence": 0.98
   }
   ```

---

## 5. Security & Isolation Model

- **Sandboxing**: Generated code is executed in an isolated runtime (Docker or confined subprocess) with CPU/memory limits and aggressive execution timeouts.
- **Path Traversal Prevention**: File tools canonicalize paths and verify `resolved_path.relative_to(workspace_root)`. Any attempt to write outside the workspace generates an immediate `PermissionError`.
- **Secret Redaction**: Inputs and outputs pass through `redact_secrets()`, ensuring tokens matching `ghp_`, `sk-`, `AWS_`, or private keys never reach logs or model prompts.
- **Command Policy Engine**: Commands are checked against an explicit allowlist and denylist. Forbidden commands like `rm -rf /` or `mkfs` are blocked unconditionally.

---

## 6. Antigravity Artifacts Specification

ForgeAgent writes Antigravity Verifiable Artifacts to `.agents/artifacts/`:
1. `implementation_plan.md`: Phased task breakdown and acceptance criteria.
2. `walkthrough.md`: Summary of changes, modified files, and verification results.
3. `verification_report.md`: Detailed test run output, passing/failing tests, and exit codes.
4. `code_review.md`: Formal security and architectural review sign-off.

# Security Threat Model: ForgeAgent for Antigravity

**Document ID:** SEC-TM-2026-001  
**Classification:** Confidential / Public Architecture Standard  
**System:** ForgeAgent Autonomous Software Engineering Integration  

---

## 1. System Overview & Trust Boundaries

ForgeAgent interacts with three distinct security zones:
1. **User / Host Boundary**: Developer host machine running Antigravity IDE/CLI and managing global credentials (`GITHUB_TOKEN`, API keys).
2. **Untrusted Code Execution Boundary (The Sandbox)**: Workspace directory containing third-party dependencies, generated source code, user inputs, and test execution environments.
3. **External Services Boundary**: Remote GitHub API, CI/CD runners, and LLM inference endpoints.

```text
 [Host Environment] 
   │  (High Trust: credentials, system binaries, user approval)
   ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  ForgeAgent Core Engine & MCP Server                        │
 │  - Policy Gate (Assisted / Autonomous / Safe Production)    │
 │  - Secret Masking Filter (Regex Redactor)                   │
 └──────────────────────────────┬──────────────────────────────┘
                                │
               Command Allowlist & Path Jail
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  Execution Sandbox (Docker / Isolated Process)              │
 │  (Low Trust: untrusted code, npm/pip packages, build tools) │
 └─────────────────────────────────────────────────────────────┘
```

---

## 2. Threat Analysis & Mitigations

### 2.1 Prompt Injection & Indirect Prompt Injection
- **Threat**: Malicious comments inside existing repository files (e.g. `README.md`, issues, comments) instructing the LLM to ignore safety rules, exfiltrate data, or delete files.
- **Mitigation**:
  - Strict hierarchical separation: System instructions and security policies are immutable and loaded out-of-band.
  - Repository content is treated strictly as passive data inside labeled XML/Markdown blocks.
  - No prompt instruction from workspace code can bypass the hardcoded `BaseTool.execute()` permission checks.

### 2.2 Arbitrary Command Execution & Sandbox Escape
- **Threat**: Generated code executing malicious shell commands (`rm -rf /`, format disks, reverse shells).
- **Mitigation**:
  - `RunCommandTool` evaluates every command against an explicit allowlist of build/test tools and a strict denylist.
  - Working directory is jailed: paths must resolve within `workspace_root`.
  - Process execution runs with timeouts (default 120s) and non-root sandbox privileges.

### 2.3 Credential Theft & Secret Leakage
- **Threat**: Accidental leakage of `GITHUB_TOKEN`, API keys, SSH private keys in LLM prompts, terminal logs, or git commits.
- **Mitigation**:
  - Environment scrubbing: subprocess environments strip parent API tokens.
  - `redact_secrets()` automatically scans all tool outputs, logs, and messages using high-entropy regex patterns (`ghp_`, `sk-`, `BEGIN PRIVATE KEY`, etc.).
  - Git pre-commit inspection verifies no private keys or high-entropy credentials exist in staged changes.

### 2.4 Destructive Git Operations
- **Threat**: Autonomous agent force-pushing to `main` or deleting release branches.
- **Mitigation**:
  - `GitConfig.protected_branches` blocks `main`, `master`, and `production`.
  - `force_push` is forbidden by default and hard-blocked in `Safe Production` mode.

### 2.5 Malicious Dependencies & Supply Chain Attacks
- **Threat**: Typosquatting or dependency confusion attacks via package manager installs.
- **Mitigation**:
  - Dependency installations must be declared in formal manifests (`package.json`, `requirements.txt`).
  - Package installations run isolated in the sandbox without access to host credentials.

### 2.6 GitHub Token Abuse & Resource Spam
- **Threat**: Agent looping and creating hundreds of repositories or PRs.
- **Mitigation**:
  - Loop guardrails: `max_iterations: 10`, max runtime limit, and idempotency checks before repository or branch creation.

---

## 3. Residual Risk Assessment

| Risk Vector | Likelihood | Impact | Residual Risk | Current Control |
|---|---|---|---|---|
| Zero-Day Sandbox Escape | Low | High | Low | Docker isolation + process boundaries |
| Sophisticated Prompt Injection | Medium | Medium | Low | Hardcoded Python tool gates (LLM has no direct syscalls) |
| Excessive Token Consumption | Medium | Low | Low | Configurable token budget (`token_budget: 500,000`) |

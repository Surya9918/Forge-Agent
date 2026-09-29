# Changelog

All notable changes to **ForgeAgent** are documented in this file.
This project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-09-26 (Production-Ready Release)

### Added
- **Canonical Domain Models:** Established `forgeagent.domain.models` unifying `PlanTask`, `DevelopmentPlan`, `CodeAction`, `TaskImplementation`, and `RepairPatch` across the entire pipeline.
- **Unmocked Real End-to-End Pipeline Test:** Added `tests/e2e/test_real_pipeline.py` executing real code generation, defect injection, test execution, autonomous repair, and Git commit.
- **Prompt Injection Defense Architecture:** Implemented passive context isolation, strict policy gatekeepers, and authored `docs/security/prompt-injection.md`.
- **Targeted Regression Test Suite:** Added `tests/unit/test_domain_schemas.py` and `tests/unit/test_regression_coder_debugger.py`.
- **Expanded CLI Companion:** Added `forge plan`, `forge develop`, and `forge test` commands with interactive Rich UI tables.
- **Dual Pydantic Compatibility:** Added `forgeagent.compat` layer supporting both Pydantic v1 (1.10.x) and Pydantic v2.
- **Benchmark Suite:** Fully operational 7-level evaluation runner in `benchmarks/runner.py` achieving 100.0% autonomous pass rate.

### Fixed
- **Problem A (Coder Schema Mismatch):** Fixed `AttributeError: 'TaskImplementation' object has no attribute 'actions'` by ensuring canonical model instantiation and safe action extraction in `CoderAgent.run()`.
- **Problem B (Debugger Schema Mismatch):** Fixed `AttributeError: 'RepairPatch' object has no attribute 'file_path'` by establishing a canonical repair patch contract and safe patch attribute access in `DebuggerAgent.run()`.
- **Project Test Discovery:** Enhanced `ProjectDetector` to discover Python projects without configuration files by checking for `.py` source and test files.
- **MCP Tool Dispatching:** Hardened MCP JSON-RPC parameter validation and structured response output.

---

## [0.1.0] - 2026-09-26 (Initial Release)
- Initial architecture with Antigravity MCP Server and Verifiable Artifacts generator.
- Multi-provider LLM abstraction (Google Gemini, OpenAI, Anthropic, Ollama, Mock).
- Tool registry with 25+ permission-checked filesystem, terminal, and git tools.
- State persistence and event bus.

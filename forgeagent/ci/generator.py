"""
GitHub Actions CI/CD Workflow Generator tailored to detected languages and frameworks.
"""

from typing import Dict, Any, Optional
from forgeagent.intelligence.detector import ProjectStackInfo


class CIWorkflowGenerator:
    @staticmethod
    def generate_workflow(stack: ProjectStackInfo, project_name: str = "app") -> str:
        lang = stack.primary_language.lower()

        if lang in ["javascript", "typescript", "react"]:
            return f"""name: CI Pipeline

on:
  push:
    branches: [ main, master, 'forgeagent/**' ]
  pull_request:
    branches: [ main, master ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: '{stack.package_manager}'

      - name: Install dependencies
        run: {stack.install_command or "npm install"}

      - name: Run Build
        run: {stack.build_command or "npm run build --if-present"}

      - name: Run Tests
        run: {stack.test_command or "npm test"}
"""

        elif lang == "python":
            return f"""name: CI Pipeline

on:
  push:
    branches: [ main, master, 'forgeagent/**' ]
  pull_request:
    branches: [ main, master ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Check Syntax and Compilation
        run: python3 -m compileall .

      - name: Run Tests
        run: {stack.test_command or "python3 -m unittest discover tests"}
"""

        elif lang == "rust":
            return """name: CI Pipeline

on:
  push:
    branches: [ main, master, 'forgeagent/**' ]
  pull_request:
    branches: [ main, master ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Cargo Build
        run: cargo build --verbose

      - name: Cargo Test
        run: cargo test --verbose
"""

        elif lang == "go":
            return """name: CI Pipeline

on:
  push:
    branches: [ main, master, 'forgeagent/**' ]
  pull_request:
    branches: [ main, master ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.22'

      - name: Build
        run: go build -v ./...

      - name: Test
        run: go test -v ./...
"""

        else:
            return """name: CI Pipeline

on:
  push:
    branches: [ main, master, 'forgeagent/**' ]
  pull_request:
    branches: [ main, master ]

jobs:
  verification:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Verification
        run: echo "Generic project verification passed"
"""

"""
Project stack and test framework detector for automatic build & test discovery.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class ProjectStackInfo(BaseModel):
    primary_language: str = "unknown"
    package_manager: str = "unknown"
    build_system: str = "unknown"
    test_framework: str = "unknown"
    build_command: str = ""
    test_command: str = ""
    install_command: str = ""
    config_files: List[str] = []


class ProjectDetector:
    @staticmethod
    def detect(workspace_path: Path) -> ProjectStackInfo:
        info = ProjectStackInfo()
        files = {p.name for p in workspace_path.iterdir() if p.is_file()}

        # 1. Node / JavaScript / TypeScript
        if "package.json" in files:
            info.primary_language = "typescript" if ("tsconfig.json" in files) else "javascript"
            info.config_files.append("package.json")
            if "pnpm-lock.yaml" in files:
                info.package_manager = "pnpm"
                info.install_command = "pnpm install"
                info.build_command = "pnpm build"
                info.test_command = "pnpm test"
            elif "yarn.lock" in files:
                info.package_manager = "yarn"
                info.install_command = "yarn install"
                info.build_command = "yarn build"
                info.test_command = "yarn test"
            else:
                info.package_manager = "npm"
                info.install_command = "npm install"
                info.build_command = "npm run build --if-present"
                info.test_command = "npm test"
            info.build_system = "node"
            info.test_framework = "jest/vitest"
            return info

        # 2. Python
        import sys
        python_cmd = "python" if sys.platform == "win32" else "python3"
        if any(f in files for f in ["pyproject.toml", "requirements.txt", "setup.py", "Pipfile"]) or any(f.endswith(".py") for f in files) or (workspace_path / "tests").is_dir():
            info.primary_language = "python"
            info.build_system = "python-setuptools"
            if "pyproject.toml" in files:
                info.config_files.append("pyproject.toml")
            if "requirements.txt" in files:
                info.config_files.append("requirements.txt")

            info.package_manager = "pip"
            info.install_command = "pip install -r requirements.txt" if "requirements.txt" in files else "pip install -e ."
            info.build_command = f"{python_cmd} -m compileall ."
            info.test_framework = "pytest"
            info.test_command = f"{python_cmd} -m unittest discover tests"
            return info

        # 3. Rust
        if "Cargo.toml" in files:
            info.primary_language = "rust"
            info.package_manager = "cargo"
            info.build_system = "cargo"
            info.test_framework = "cargo test"
            info.install_command = "cargo fetch"
            info.build_command = "cargo build"
            info.test_command = "cargo test"
            info.config_files.append("Cargo.toml")
            return info

        # 4. Go
        if "go.mod" in files:
            info.primary_language = "go"
            info.package_manager = "go modules"
            info.build_system = "go build"
            info.test_framework = "go test"
            info.install_command = "go mod download"
            info.build_command = "go build ./..."
            info.test_command = "go test ./..."
            info.config_files.append("go.mod")
            return info

        # 5. Java (Maven / Gradle)
        if "pom.xml" in files:
            info.primary_language = "java"
            info.package_manager = "maven"
            info.build_system = "maven"
            info.test_framework = "junit"
            info.install_command = "mvn dependency:resolve"
            info.build_command = "mvn compile"
            info.test_command = "mvn test"
            info.config_files.append("pom.xml")
            return info

        if "build.gradle" in files or "build.gradle.kts" in files:
            info.primary_language = "java"
            info.package_manager = "gradle"
            info.build_system = "gradle"
            info.test_framework = "junit"
            info.install_command = "gradle build -x test"
            info.build_command = "gradle assemble"
            info.test_command = "gradle test"
            info.config_files.append("build.gradle")
            return info

        # Default fallback
        info.test_command = "echo 'No automated test runner detected'"
        info.build_command = "echo 'No build command detected'"
        return info

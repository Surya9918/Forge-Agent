from setuptools import setup, find_packages

setup(
    name="forgeagent",
    version="0.1.0",
    description="Autonomous Software Engineering inside Antigravity",
    long_description=open("README.md", "r", encoding="utf-8").read() if open("README.md").readable() else "",
    long_description_content_type="text/markdown",
    author="ForgeAgent Engineering Team",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "click>=8.0.0",
        "rich>=13.0.0",
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "forge=forgeagent.cli.main:cli",
            "forge-mcp=forgeagent.antigravity.mcp_server:main",
        ],
    },
    python_requires=">=3.9",
)

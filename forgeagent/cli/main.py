"""
ForgeAgent CLI Companion: High-level autonomous command-line interface.
"""

import sys
import json
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from forgeagent.config.loader import load_config
from forgeagent.agents.orchestrator import AgentOrchestrator
from forgeagent.state.persistence import StateManager
from forgeagent.state.state import AgentPhase
from forgeagent.events.bus import bus
from forgeagent.events.events import ForgeEvent, EventType
from forgeagent.antigravity.mcp_server import ForgeMCPServer

console = Console()


def render_banner():
    console.print(Panel.fit(
        "[bold cyan]FORGEAGENT[/bold cyan] — [italic green]Autonomous Software Engineering inside Antigravity[/italic green]\n"
        "[dim]Engineered for Google Antigravity 2.0, IDE, and CLI[/dim]",
        border_style="cyan"
    ))


@click.group()
def cli():
    """ForgeAgent CLI — Autonomous Software Engineering Companion."""
    pass


@cli.command()
@click.argument("requirement")
@click.option("--name", "-n", default="autonomous-app", help="Project identifier name")
@click.option("--mode", "-m", default="autonomous", type=click.Choice(["assisted", "autonomous", "safe_production"]), help="Autonomy mode")
def create(requirement: str, name: str, mode: str):
    """Create a new project from a high-level requirement and run autonomous engineering."""
    render_banner()
    config = load_config(overrides={"project": {"name": name}, "agent": {"mode": mode}})
    orchestrator = AgentOrchestrator(config)

    # Event hook for rich terminal output
    def on_event(event: ForgeEvent):
        if event.event_type == EventType.TASK_STARTED:
            console.print(f"[bold blue]● Task Started:[/bold blue] {event.message}")
        elif event.event_type == EventType.FILE_CREATED:
            console.print(f"  [green]+[/green] {event.message}")
        elif event.event_type == EventType.TEST_PASSED:
            console.print(f"[bold green]✓ Tests Passed:[/bold green] {event.message}")
        elif event.event_type == EventType.TEST_FAILED:
            console.print(f"[bold yellow]✗ Test Failure:[/bold yellow] {event.message}")
        elif event.event_type == EventType.FIX_APPLIED:
            console.print(f"[bold magenta]⚡ Self-Healing Repair:[/bold magenta] {event.message}")
        elif event.event_type == EventType.COMMIT_CREATED:
            console.print(f"[bold cyan]◈ Git Commit:[/bold cyan] {event.message}")
        elif event.event_type == EventType.PR_CREATED:
            console.print(f"[bold bright_green]★ GitHub PR Opened:[/bold bright_green] {event.message}")
        elif event.event_type == EventType.PROJECT_COMPLETED:
            console.print(f"[bold green]✔ Pipeline Succeeded:[/bold green] {event.message}")

    bus.subscribe_all(on_event)

    console.print(f"[bold]Requirement:[/bold] {requirement}")
    console.print(f"[bold]Project Name:[/bold] {name} | [bold]Mode:[/bold] {mode}")
    console.print("[dim]Starting autonomous software engineering loop...[/dim]\n")

    state = orchestrator.run(requirement=requirement, project_name=name)

    # Final summary display
    table = Table(title="ForgeAgent Execution Summary", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="dim")
    table.add_column("Value", style="bold")
    table.add_row("Task ID", state.task_id)
    table.add_row("Status", state.phase.value)
    table.add_row("Status Message", state.status_message)
    table.add_row("Git Branch", state.branch or "N/A")
    table.add_row("Commit SHA", state.commit_sha or "N/A")
    table.add_row("Tests Passed", str(state.tests.passed))
    table.add_row("Tests Failed", str(state.tests.failed))
    table.add_row("GitHub PR", state.pr_url or "N/A")
    table.add_row("Files Modified", str(len(state.changed_files)))
    table.add_row("Self-Healing Iterations", str(state.iteration))
    console.print(table)


@cli.command()
def run():
    """Resume execution of the latest saved project state."""
    config = load_config()
    state_manager = StateManager(f"{config.project.workspace}/.forge/state")
    latest = state_manager.load_latest()
    if not latest:
        console.print("[red]No active or previous task state found to run.[/red]")
        return
    orchestrator = AgentOrchestrator(config)
    console.print(f"[green]Resuming task {latest.task_id} from phase '{latest.phase}'...[/green]")
    orchestrator.run(latest.requirement, latest.project_id)


@cli.command()
def status():
    """Display real-time status of the current or latest ForgeAgent task."""
    config = load_config()
    state_manager = StateManager(f"{config.project.workspace}/.forge/state")
    state = state_manager.load_latest()
    if not state:
        console.print("[yellow]No active task state found.[/yellow]")
        return

    table = Table(title="ForgeAgent Active Status", show_header=True)
    table.add_column("Field", style="cyan")
    table.add_column("Details", style="white")
    table.add_row("Project", state.project_id)
    table.add_row("Phase", state.phase.value.upper())
    table.add_row("Message", state.status_message)
    table.add_row("Iteration", f"{state.iteration} / {state.max_iterations}")
    table.add_row("Tests", f"✓ {state.tests.passed} passed | ✗ {state.tests.failed} failed")
    table.add_row("Branch", state.branch or "main")
    table.add_row("PR", state.pr_url or "None")
    console.print(table)


@cli.command()
def pause():
    """Pause autonomous execution."""
    config = load_config()
    state_manager = StateManager(f"{config.project.workspace}/.forge/state")
    state = state_manager.load_latest()
    if state:
        state.phase = AgentPhase.PAUSED
        state.status_message = "Execution paused by user request"
        state_manager.save(state)
        console.print("[yellow]ForgeAgent paused successfully.[/yellow]")


@cli.command()
def resume():
    """Resume a paused ForgeAgent task."""
    config = load_config()
    state_manager = StateManager(f"{config.project.workspace}/.forge/state")
    state = state_manager.load_latest()
    if state and state.phase == AgentPhase.PAUSED:
        state.phase = AgentPhase.IMPLEMENTATION
        state_manager.save(state)
        console.print("[green]ForgeAgent resumed.[/green]")
        orchestrator = AgentOrchestrator(config)
        orchestrator.run(state.requirement, state.project_id)


@cli.command()
def approve():
    """Approve a pending action in Assisted Mode."""
    config = load_config()
    state_manager = StateManager(f"{config.project.workspace}/.forge/state")
    state = state_manager.load_latest()
    if state and state.phase == AgentPhase.BLOCKED:
        state.phase = AgentPhase.IMPLEMENTATION
        state.status_message = "Human approval granted. Resuming execution."
        state_manager.save(state)
        console.print("[green]Approval registered. ForgeAgent continuing work.[/green]")


@cli.command()
def stop():
    """Stop active execution and reset state to IDLE."""
    config = load_config()
    state_manager = StateManager(f"{config.project.workspace}/.forge/state")
    state = state_manager.load_latest()
    if state:
        state.phase = AgentPhase.IDLE
        state.status_message = "Execution stopped by user."
        state_manager.save(state)
        console.print("[red]ForgeAgent execution stopped.[/red]")


@cli.command(name="mcp")
def mcp():
    """Start ForgeAgent Model Context Protocol (MCP) server on stdio for Antigravity."""
    server = ForgeMCPServer()
    server.run_stdio()


if __name__ == "__main__":
    cli()

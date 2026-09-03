from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.live import Live
from rich.spinner import Spinner

console = Console()

def render_banner():
    console.print(Panel.fit(
        "[bold cyan]AutoEnv V1.0[/bold cyan] [dim]— Runtime Environment & Container Engine[/dim]",
        border_style="cyan"
    ))

def create_dependency_tree(deps):
    tree = Tree("[bold green]Captured Dependency Tree[/bold green]")
    for dep in deps:
        tree.add(f"[cyan]📦 {dep}[/cyan] [dim](Resolved via Runtime Trace)[/dim]")
    return tree
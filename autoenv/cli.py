import click
import sys
import runpy
from time import sleep
from rich.console import Console
from rich.spinner import Spinner
from rich.panel import Panel
from autoenv.tracer import start_tracing, get_dependencies
from autoenv.sanitizer import scan_file_for_secrets, generate_env_example
from autoenv.ui import render_banner, create_dependency_tree

console = Console()

@click.group()
def cli():
    """AutoEnv: Capture running runtime dependencies and generate containers instantly."""
    pass

@cli.command()
@click.option('--run', '-r', required=True, help='Path to the target Python script to trace.')
def capture(run):
    """Trace target execution, perform security pre-flight checks, and compile artifacts."""
    render_banner()
    
    with console.status("[bold yellow]Running security pre-flight check..."):
        sleep(0.6)
        if scan_file_for_secrets(run):
            console.print("[bold red][!] SECURITY WARNING: Potential hardcoded API keys or secrets detected![/bold red]")
            sys.exit(1)
            
    console.print("[bold green][✔] Security check passed:[/bold green] No hardcoded secrets found.")
    
    console.print(f"\n[bold blue][*] Initializing AutoEnv runtime recorder for:[/bold blue] {run}")
    start_tracing()
    
    try:
        runpy.run_path(run, run_name="__main__")
    except Exception as e:
        console.print(f"[bold red][!] Target script execution failed: {e}[/bold red]")
        sys.exit(1)
        
    with console.status("[bold cyan]Analyzing runtime dependency graph..."):
        sleep(0.8)
        deps = get_dependencies()
    
    # Render Rich Tree View
    console.print()
    console.print(create_dependency_tree(deps))
    console.print()
    
    # Write requirements & artifacts
    req_filename = "generated_requirements.txt"
    with open(req_filename, "w") as f:
        for dep in deps:
            f.write(f"{dep}\n")
            
    generate_env_example()
    
    dockerfile_content = f"""FROM python:3.11-slim
WORKDIR /app
COPY {req_filename} .
RUN pip install -r {req_filename}
COPY . .
CMD ["python", "{run}"]
"""
    
    docker_filename = "Dockerfile.autoenv"
    with open(docker_filename, "w") as f:
        f.write(dockerfile_content)
        
    console.print(Panel(
        f"[bold green]SUCCESS: Environment captured safely![/bold green]\n\n"
        f" • [cyan]{req_filename}[/cyan]\n"
        f" • [cyan].env.example[/cyan]\n"
        f" • [cyan]{docker_filename}[/cyan]",
        title="[bold]Artifact Generation Complete[/bold]",
        border_style="green"
    ))

if __name__ == "__main__":
    cli()
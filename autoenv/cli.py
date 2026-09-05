import click
import sys
import os
import runpy
import json
from time import sleep
from rich.console import Console
from rich.panel import Panel
from autoenv.tracer import start_tracing, get_dependencies
from autoenv.sanitizer import scan_file_for_secrets, generate_env_example
from autoenv.ui import render_banner, create_dependency_tree
from autoenv.system_deps import resolve_system_dependencies
from autoenv.core import run_headless_capture
from autoenv.policy import evaluate_compliance
from autoenv.sbom import generate_cyclonedx_sbom
from autoenv.scanner import scan_dependencies_for_cves
from autoenv.notifier import post_pr_comment

console = Console()

@click.group()
def cli():
    """AutoEnv: Capture running runtime dependencies and generate containers instantly."""
    pass

@cli.command()
@click.option('--run', '-r', help='Path to target Python script')
@click.option('--module', '-m', help='Target Python module')
@click.option('--json', 'output_json', is_flag=True, help='Output machine-readable JSON results')
@click.argument('args', nargs=-1)
def capture(run, module, output_json, args):
    """Trace execution, perform security checks, and compile artifacts."""
    result = run_headless_capture(run=run, module=module, args=args)
    
    report_filename = "autoenv_report.json"
    with open(report_filename, "w") as f:
        json.dump(result, f, indent=2)

    if output_json:
        click.echo(json.dumps(result, indent=2))
        sys.exit(0 if result["success"] else 1)

    if not result["success"]:
        click.echo(f"[!] Execution failed: {result.get('error', 'Unknown error')}", err=True)
        sys.exit(1)

    target = run if run else module
    render_banner()
    
    if run:
        with console.status("[bold yellow]Running security pre-flight check..."):
            sleep(0.6)
            if scan_file_for_secrets(run):
                console.print("[bold red][!] SECURITY WARNING: Potential hardcoded API keys detected![/bold red]")
                sys.exit(1)
        console.print("[bold green][✔] Security check passed:[/bold green] No hardcoded secrets found.")
    
    console.print(f"\n[bold blue][*] Initializing AutoEnv runtime recorder for:[/bold blue] {target} {args}")
    
    sys.argv = [target] + list(args)
    sys.path.insert(0, os.getcwd())

    start_tracing()
    
    try:
        if run:
            runpy.run_path(run, run_name="__main__")
        elif module:
            runpy.run_module(module, run_name="__main__", alter_sys=True)
    except SystemExit as e:
        if e.code != 0:
            console.print(f"[bold red][!] Execution terminated with code {e.code}[/bold red]")
    except Exception as e:
        console.print(f"[bold red][!] Execution failed: {e}[/bold red]")
        sys.exit(1)
        
    with console.status("[bold cyan]Analyzing runtime dependency graph..."):
        sleep(0.8)
        deps = get_dependencies()
    
    console.print("\n", create_dependency_tree(deps), "\n")
    
    req_filename = "generated_requirements.txt"
    with open(req_filename, "w") as f:
        for dep in deps:
            f.write(f"{dep}\n")
            
    generate_env_example()
    sbom_path = generate_cyclonedx_sbom(deps)
    sys_deps = resolve_system_dependencies(deps)
    
    apt_get_instruction = ""
    if sys_deps:
        sys_deps_str = " ".join(sys_deps)
        apt_get_instruction = f"RUN apt-get update && apt-get install -y {sys_deps_str} && rm -rf /var/lib/apt/lists/*\n"
    
    cmd_instruction = f'CMD ["python", "{run}"]' if run else f'CMD ["python", "-m", "{module}", "{" ".join(args)}"]'
    
    dockerfile_content = f"""FROM python:3.11-slim
WORKDIR /app

{apt_get_instruction}COPY {req_filename} .
RUN pip install --no-cache-dir -r {req_filename}

COPY . .
{cmd_instruction}
"""
    
    docker_filename = "Dockerfile.autoenv"
    with open(docker_filename, "w") as f:
        f.write(dockerfile_content)
        
    console.print(Panel(
        f"[bold green]SUCCESS: Multi-file environment captured safely![/bold green]\n\n"
        f" • [cyan]{req_filename}[/cyan] (Smart filtered)\n"
        f" • [cyan].env.example[/cyan]\n"
        f" • [cyan]{docker_filename}[/cyan]\n"
        f" • [cyan]{sbom_path}[/cyan] (CycloneDX SBOM)",
        title="[bold]Artifact Generation Complete[/bold]",
        border_style="green"
    ))

@cli.command()
@click.option('--report', default='autoenv_report.json', help='Path to autoenv JSON report')
@click.option('--policy', default='autoenv_policy.json', help='Path to policy configuration file')
def check_policy(report, policy):
    """Evaluate captured runtime dependencies against corporate compliance policies."""
    result = evaluate_compliance(report_path=report, policy_path=policy)
    
    if result["compliant"]:
        click.secho("Compliance check passed successfully!", fg="green")
        sys.exit(0)
    else:
        click.secho("Compliance check failed with policy violations:", fg="red")
        for v in result["violations"]:
            click.secho(f"  - {v}", fg="yellow")
        sys.exit(1)

@cli.command()
@click.option('--output', '-o', default='sbom.json', help='Path to output SBOM file')
def sbom(output):
    """Generate an industry-standard CycloneDX SBOM from local execution state."""
    deps = get_dependencies()
    path = generate_cyclonedx_sbom(deps, output_path=output)
    click.secho(f"CycloneDX SBOM generated successfully at: {path}", fg="green")

@cli.command()
@click.option('--sbom', default='sbom.json', help='Path to SBOM file')
def scan_cves(sbom):
    """Scan SBOM components against the OSV database for known CVEs."""
    click.echo("[*] Scanning dependencies for known vulnerabilities...")
    result = scan_dependencies_for_cves(sbom_path=sbom)
    
    if result.get("error"):
        click.secho(f"Warning: Could not complete CVE scan: {result['error']}", fg="yellow")
        sys.exit(0)
        
    if result["vulnerabilities_found"]:
        click.secho("[!] SECURITY ALERT: Vulnerabilities detected!", fg="red")
        for vuln in result["vulnerabilities"]:
            click.secho(f"  - [{vuln['id']}] {vuln['package']}: {vuln['summary']}", fg="yellow")
        sys.exit(1)
    else:
        click.secho("[✔] No known vulnerabilities found in SBOM components.", fg="green")
        sys.exit(0)

@cli.command()
def comment_pr():
    """Post audit summary as a Markdown comment on the active GitHub Pull Request."""
    post_pr_comment()

if __name__ == "__main__":
    cli()
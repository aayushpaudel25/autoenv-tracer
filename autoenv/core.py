import os
import sys
import runpy
import io
from contextlib import redirect_stdout, redirect_stderr
from autoenv.tracer import start_tracing, get_dependencies
from autoenv.sanitizer import scan_file_for_secrets
from autoenv.system_deps import resolve_system_dependencies
from autoenv.sbom import generate_cyclonedx_sbom

def run_headless_capture(run=None, module=None, args=None):
    """
    Runs the AutoEnv capture engine programmatically without UI elements.
    Returns a structured dictionary of findings for CI/CD pipelines.
    """
    args = args or []
    target = run if run else module
    
    if not target:
        return {"success": False, "error": "No target script or module specified."}

    # 1. Security Pre-flight Check
    if run and os.path.exists(run):
        if scan_file_for_secrets(run):
            return {
                "success": False,
                "error": "Security violation: Hardcoded API keys or secrets detected.",
                "security_failed": True
            }

    # 2. Setup execution context
    sys.argv = [target] + list(args)
    sys.path.insert(0, os.getcwd())

    start_tracing()
    
    # Suppress target script's printed output from polluting stdout JSON stream
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            if run:
                runpy.run_path(run, run_name="__main__")
            elif module:
                runpy.run_module(module, run_name="__main__", alter_sys=True)
    except SystemExit as e:
        if e.code != 0:
            return {"success": False, "error": f"Execution terminated with code {e.code}"}
    except Exception as e:
        return {"success": False, "error": f"Execution failed: {str(e)}"}

    # 3. Gather dependencies and resolve system packages
    deps = sorted(list(get_dependencies()))
    sys_deps = resolve_system_dependencies(deps)
    
    # Generate CycloneDX SBOM
    sbom_path = generate_cyclonedx_sbom(deps)

    return {
        "success": True,
        "target": target,
        "dependencies": deps,
        "system_dependencies": sys_deps,
        "sbom_file": sbom_path
    }
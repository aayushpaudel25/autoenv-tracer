import json
import importlib.metadata
import datetime

def generate_cyclonedx_sbom(dependencies, output_path="sbom.json"):
    """
    Generates an industry-standard CycloneDX JSON SBOM from runtime dependencies,
    resolving package versions using importlib.metadata.
    """
    components = []
    for dep in dependencies:
        version = "unknown"
        try:
            version = importlib.metadata.version(dep)
        except importlib.metadata.PackageNotFoundError:
            pass
        
        components.append({
            "type": "library",
            "name": dep,
            "version": version,
            "purl": f"pkg:pypi/{dep}@{version}"
        })

    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "version": 1,
        "metadata": {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "tools": [
                {
                    "vendor": "AutoEnv",
                    "name": "autoenv-cli",
                    "version": "0.1.0"
                }
            ]
        },
        "components": components
    }

    with open(output_path, "w") as f:
        json.dump(sbom, f, indent=2)
    
    return output_path
import json
import urllib.request
import urllib.error

OSV_API_URL = "https://api.osv.dev/v1/querybatch"

def scan_dependencies_for_cves(sbom_path="sbom.json"):
    """
    Queries the OSV API using SBOM components to detect known security vulnerabilities.
    """
    try:
        with open(sbom_path, "r") as f:
            sbom = json.load(f)
    except FileNotFoundError:
        return {"vulnerabilities_found": False, "details": "SBOM file not found."}

    components = sbom.get("components", [])
    if not components:
        return {"vulnerabilities_found": False, "vulnerabilities": []}

    queries = []
    for comp in components:
        name = comp.get("name")
        version = comp.get("version")
        if version and version != "unknown":
            queries.append({
                "package": {"name": name, "ecosystem": "PyPI"},
                "version": version
            })

    if not queries:
        return {"vulnerabilities_found": False, "vulnerabilities": []}

    payload = json.dumps({"queries": queries}).encode("utf-8")
    req = urllib.request.Request(
        OSV_API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return {"vulnerabilities_found": False, "error": str(e)}

    vulnerabilities = []
    results = result.get("results", [])
    for idx, res in enumerate(results):
        vulns = res.get("vulns", [])
        if vulns:
            pkg_name = queries[idx]["package"]["name"]
            for v in vulns:
                vulnerabilities.append({
                    "package": pkg_name,
                    "id": v.get("id"),
                    "summary": v.get("summary", "No summary provided.")
                })

    return {
        "vulnerabilities_found": len(vulnerabilities) > 0,
        "vulnerabilities": vulnerabilities
    }
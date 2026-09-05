import os
import json
import urllib.request

def post_pr_comment(report_path="autoenv_report.json", sbom_path="sbom.json"):
    """
    Posts a formatted Markdown summary table of AutoEnv audit findings 
    as a comment on the active GitHub Pull Request.
    """
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    event_path = os.environ.get("GITHUB_EVENT_PATH")

    if not token or not repo or not event_path:
        print("[*] Skipping PR comment: Not running in a GitHub PR action environment.")
        return

    try:
        with open(event_path, "r") as f:
            event_data = json.load(f)
        pr_number = event_data.get("pull_request", {}).get("number")
        if not pr_number:
            print("[*] Skipping PR comment: Not a pull request event.")
            return
    except Exception as e:
        print(f"[!] Could not read GitHub event payload: {e}")
        return

    # Load report and SBOM data
    try:
        with open(report_path, "r") as f:
            report = json.load(f)
    except Exception:
        report = {}

    try:
        with open(sbom_path, "r") as f:
            sbom = json.load(f)
    except Exception:
        sbom = {}

    deps = report.get("dependencies", [])
    sys_deps = report.get("system_dependencies", [])
    components = sbom.get("components", [])

    # Build Markdown Body
    comment_body = "### 🛡️ AutoEnv Enterprise Compliance Audit\n\n"
    comment_body += f"**Target:** `{report.get('target', 'Unknown')}`\n"
    comment_body += f"**Status:** `{'PASSED ✅' if report.get('success') else 'FAILED ❌'}`\n\n"

    comment_body += "#### 📦 Runtime Python Dependencies\n"
    if deps:
        comment_body += "| Package | Version | PURL |\n|---|---|---|\n"
        comp_map = {c["name"]: c.get("version", "unknown") for c in components}
        for dep in deps:
            ver = comp_map.get(dep, "unknown")
            comment_body += f"| `{dep}` | `{ver}` | `pkg:pypi/{dep}@{ver}` |\n"
    else:
        comment_body += "_No external runtime dependencies tracked._\n"

    comment_body += "\n#### 🐧 Resolved System Packages (Apt)\n"
    if sys_deps:
        comment_body += ", ".join([f"`{pkg}`" for pkg in sys_deps])
    else:
        comment_body += "_None required._\n"

    comment_body += "\n***\n*Automated by **AutoEnv** Compliance Gatekeeper Engine.*"

    # Post to GitHub PR API
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    payload = json.dumps({"body": comment_body}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 201:
                print("[✔] Successfully posted compliance report to Pull Request.")
            else:
                print(f"[!] Failed to post PR comment. Status code: {response.status}")
    except Exception as e:
        print(f"[!] Error posting PR comment: {e}")
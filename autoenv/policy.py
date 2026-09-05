import json
import os

DEFAULT_POLICY = {
    "allowed_packages": [],  # Empty means all allowed unless blocked
    "blocked_packages": ["telnetlib", "pickle"],  # Example insecure modules
    "blocked_system_dependencies": ["netcat"],    # Example restricted system binaries
    "require_security_clean": True
}

def load_policy(policy_path="autoenv_policy.json"):
    """Loads a custom compliance policy file or returns defaults."""
    if os.path.exists(policy_path):
        with open(policy_path, "r") as f:
            return {**DEFAULT_POLICY, **json.load(f)}
    return DEFAULT_POLICY

def evaluate_compliance(report_path="autoenv_report.json", policy_path="autoenv_policy.json"):
    """
    Evaluates the autoenv capture report against compliance rules.
    Returns a status dict with success state and policy violations.
    """
    if not os.path.exists(report_path):
        return {"compliant": False, "violations": ["Report file not found. Run capture first."]}

    with open(report_path, "r") as f:
        report = json.load(f)

    if not report.get("success", False):
        return {
            "compliant": False,
            "violations": [report.get("error", "Unknown execution failure.")]
        }

    policy = load_policy(policy_path)
    violations = []

    # 1. Check security pre-flight flag
    if policy.get("require_security_clean") and report.get("security_failed"):
        violations.append("Security violation: Hardcoded secrets or credentials detected in source code.")

    detected_packages = report.get("dependencies", [])
    detected_sys_deps = report.get("system_dependencies", [])

    # 2. Check blocked packages
    for pkg in detected_packages:
        if pkg in policy.get("blocked_packages", []):
            violations.append(f"Blocked package detected: '{pkg}' is prohibited by corporate policy.")

    # 3. Check allowed packages (if explicitly defined whitelist)
    allowed = policy.get("allowed_packages", [])
    if allowed:
        for pkg in detected_packages:
            if pkg not in allowed:
                violations.append(f"Unauthorized package detected: '{pkg}' is not in the approved whitelist.")

    # 4. Check blocked system dependencies
    for sys_dep in detected_sys_deps:
        if sys_dep in policy.get("blocked_system_dependencies", []):
            violations.append(f"Restricted system binary required: '{sys_dep}' violates infrastructure policy.")

    return {
        "compliant": len(violations) == 0,
        "violations": violations
    }
# AutoEnv 🚀

> Stop guessing dependencies. Capture the running reality.

AutoEnv is an enterprise-grade CLI tool that wiretaps your Python application's runtime using internal audit hooks, stripping out noise and instantly compiling a pristine, reproducible Dockerfile and secure environment configuration.

![AutoEnv Terminal Output](image_216b61.png)

## Why AutoEnv?
Developers constantly waste hours debugging environment drift—code that runs perfectly on a local machine but crashes inside a container due to missing dependencies, hidden imports, or system-level configuration mismatches. 

AutoEnv solves this by observing actual file accesses and third-party package imports *while your application runs*, guaranteeing 100% dependency accuracy.

---

## Features
- **Runtime Wiretapping:** Bypasses static code parsing by capturing true module execution via internal Python audit hooks.
- **Automated Secret Pre-Flight:** Scans source files using high-entropy regex patterns to prevent hardcoded API keys or credentials from leaking into your containers.
- **Rich Terminal UI (TUI):** Delivers a clean, real-time diagnostic dashboard complete with status indicators and dependency trees.
- **Deterministic Artifacts:** Automatically outputs clean `generated_requirements.txt`, `.env.example`, and an optimized `Dockerfile.autoenv`.

---

## Installation

Clone the repository and install it locally in editable mode:

```bash
git clone [https://github.com/aayushpaudel25/autoenv-tracer.git](https://github.com/aayushpaudel25/autoenv-tracer.git)
cd autoenv-tracer
pip install -e .
import sys

seen_dependencies = set()
seen_files = set()

# 1. Blacklist: Modules we trace, but CANNOT be installed via pip
PIP_BLACKLIST = {
    "backports",
    "pkg_resources" # Another common internal un-installable module
}

# 2. Translation Map: Maps "import_name" -> "pip_install_name"
PIP_MAPPING = {
    "socks": "PySocks",
    "PIL": "Pillow",
    "yaml": "PyYAML",
    "dotenv": "python-dotenv",
    "bs4": "beautifulsoup4"
}

def audit_hook(event, args):
    if event in ("open", "io.open"):
        file_path = str(args[0])
        ignore_paths = ('/System', '/usr/lib', '/Library', '<')
        
        if not file_path.startswith(ignore_paths) and file_path not in seen_files:
            seen_files.add(file_path)
            
    elif event == "import":
        module_name = args[0]
        base_module = module_name.split('.')[0] 
        
        if not module_name.startswith("_") and base_module not in sys.stdlib_module_names:
            if base_module not in seen_dependencies:
                seen_dependencies.add(base_module)

def start_tracing():
    sys.addaudithook(audit_hook)

def get_dependencies():
    """Cleans, translates, and returns the final list of pip packages"""
    clean_deps = set()
    for dep in seen_dependencies:
        # Skip un-installable blacklisted modules
        if dep in PIP_BLACKLIST:
            continue
        
        # Translate import name to pip name, or just keep the original
        pip_name = PIP_MAPPING.get(dep, dep)
        clean_deps.add(pip_name)
        
    return list(clean_deps)
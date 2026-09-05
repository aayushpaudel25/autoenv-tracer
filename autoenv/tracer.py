import sys
import site

# Get the paths where pip installs third-party packages
SITE_PACKAGES = site.getsitepackages()
if hasattr(site, 'getusersitepackages'):
    SITE_PACKAGES.append(site.getusersitepackages())

_captured_imports = set()

def audit_hook(event, args):
    """Listens to raw import events at the C-level."""
    if event == "import":
        _captured_imports.add(args[0])

def start_tracing():
    """Initializes the runtime wiretap."""
    sys.addaudithook(audit_hook)

def get_dependencies():
    """Filters captured modules to return ONLY third-party pip packages."""
    third_party_deps = set()
    
    # Check both dynamically captured imports and natively loaded modules
    all_modules = set(sys.modules.keys()).union(_captured_imports)
    
    for mod_name in all_modules:
        try:
            mod = sys.modules.get(mod_name)
            if not mod or not hasattr(mod, '__file__') or not mod.__file__:
                continue
            
            # If the file path lives inside a pip site-packages folder, it's a dependency
            is_third_party = any(mod.__file__.startswith(sp) for sp in SITE_PACKAGES)
            
            if is_third_party:
                # Extract the base package name (e.g., 'fastapi.routing' -> 'fastapi')
                base_pkg = mod_name.split('.')[0]
                
                # Exclude internal pip/setuptools noise and local editable hacks
                if base_pkg not in ['pip', 'setuptools', 'wheel', 'autoenv', 'rich', 'click', '_distutils_hack'] and not base_pkg.startswith('__editable__'):
                    third_party_deps.add(base_pkg)
        except Exception:
            pass
            
    return sorted(list(third_party_deps))
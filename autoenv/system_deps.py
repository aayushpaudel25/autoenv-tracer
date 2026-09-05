# autoenv/system_deps.py

# A knowledge graph mapping PyPI packages to Debian/Ubuntu system packages
SYSTEM_DEPENDENCY_MAP = {
    "psycopg2": ["libpq-dev", "gcc"],
    "psycopg2-binary": ["libpq-dev", "gcc"],
    "mysqlclient": ["default-libmysqlclient-dev", "gcc"],
    "opencv-python": ["libgl1", "libglib2.0-0"],
    "opencv-python-headless": ["libgl1", "libglib2.0-0"],
    "lxml": ["libxml2-dev", "libxslt-dev", "gcc"],
    "cffi": ["libffi-dev", "gcc"],
    "cryptography": ["libssl-dev", "libffi-dev", "gcc"],
    "Pillow": ["libjpeg-dev", "zlib1g-dev", "libfreetype6-dev"],
    "confluent-kafka": ["librdkafka-dev", "gcc"],
    "scipy": ["gfortran", "libopenblas-dev", "liblapack-dev"],
}

def resolve_system_dependencies(python_packages):
    """
    Scans the captured Python packages and returns a deduplicated list
    of required Linux system packages (apt-get).
    """
    system_packages = set()
    
    for pkg in python_packages:
        # Check if the python package requires system-level libraries
        if pkg in SYSTEM_DEPENDENCY_MAP:
            for sys_dep in SYSTEM_DEPENDENCY_MAP[pkg]:
                system_packages.add(sys_dep)
                
    return sorted(list(system_packages))
from setuptools import setup, find_packages

setup(
    name="autoenv-tracer",
    version="0.1.0",
    description="Automated enterprise-grade runtime tracer, security scanner, and container generator.",
    author="AutoEnv Contributors",
    url="https://github.com/aayushpaudel25/autoenv-tracer",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "autoenv=autoenv.cli:cli",
        ],
    },
    python_requires=">=3.11",
)

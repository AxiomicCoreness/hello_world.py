from setuptools import find_packages, setup

# Local fastMCP package removed. This setup.py no longer installs a
# fastmcp-* distribution. Keep a minimal meta package name for tooling
# that still invokes setup.py; packages= is empty until a new internal
# package is introduced.
setup(
    name="axiomic-hello-world",
    version="0.1.0",
    packages=find_packages(exclude=["tests", "tests.*", "ledger", "ledger.*"]),
    python_requires=">=3.9",
    install_requires=["fastapi>=0.109.0", "uvicorn>=0.27.0", "pydantic>=2.0"],
)

from setuptools import find_packages, setup

setup(
    name="fastmcp-garden",
    version="0.1.0",
    packages=find_packages(include=["fastMCP", "fastMCP.*"]),
    python_requires=">=3.9",
    install_requires=["fastapi>=0.109.0", "uvicorn>=0.27.0", "pydantic>=2.0"],
)

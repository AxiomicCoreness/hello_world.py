#!/usr/bin/env python3
"""
🜁∀ Sovereign Garden — Multi-Agent AI Framework
φ²-harmonic architecture with eternal anchor
"""

from setuptools import setup, find_packages

setup(
    name="sovereign-garden",
    version="0.1.0-phi",
    author="Clarke Yoursa Tee",
    description="🜁∀ Multi-Agent AI Framework — Grok & Mistral Clients Fused",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "requests>=2.31.0",
        "tenacity>=8.2.0",
        "python-dotenv>=1.0.0",
        "numpy>=1.24.0",
    ],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

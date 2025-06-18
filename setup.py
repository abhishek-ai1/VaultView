#!/usr/bin/env python3
"""
VaultView - Professional Domain Security Monitor
Setup script for package installation
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="vaultview",
    version="1.0.0",
    author="VaultView Team",
    author_email="support@vaultview.com",
    description="Professional domain security monitoring tool with SSL, DNS, WHOIS, and email diagnostics",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/vaultview",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/vaultview/issues",
        "Documentation": "https://github.com/yourusername/vaultview/docs",
        "Source Code": "https://github.com/yourusername/vaultview",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Security",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Framework :: Flask",
        "Environment :: Web Environment",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-flask>=1.2.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
        ],
        "production": [
            "gunicorn>=20.1.0",
            "gevent>=22.10.0",
        ],
        "docker": [
            "docker>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "vaultview=vaultview.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "vaultview": [
            "templates/*.html",
            "static/*.css",
            "static/js/*.js",
            "reports/templates/*.html",
        ],
    },
    keywords=[
        "security",
        "ssl",
        "dns",
        "whois",
        "blacklist",
        "email",
        "monitoring",
        "cybersecurity",
        "domain",
        "certificate",
        "flask",
        "web-application",
    ],
    platforms=["any"],
    license="MIT",
    zip_safe=False,
) 
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcchallonge",
    version="0.1.0",
    author="AutoMcG",
    description="A Python package for interacting with Challonge API and generating tournament visualizations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AutoMcG/McChallonge",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "flask>=3.0.0",
        "frozen-flask>=1.0.0",
        "requests>=2.31.0",
        "requests-oauthlib>=2.0.0",
        "jinja2>=3.1.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mcchallonge-oauth=mcchallonge.cli.challonge_oauth_cli:main",
            "mcchallonge-dashboard=mcchallonge.cli.generate_dashboard:main",
        ],
    },
)

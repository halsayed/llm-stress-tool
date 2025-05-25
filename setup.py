from setuptools import setup, find_packages

setup(
    name="llm_stress_tool",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "ray",
        "llmperf",
        "matplotlib",
        "pandas",
        "python-docx",
        "tqdm",
        "requests",
        "aiohttp",
    ],
    entry_points={
        "console_scripts": [
            "llm-stress-tool=src.main:main",
        ],
    },
)

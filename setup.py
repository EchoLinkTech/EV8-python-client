from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="echolink-client",
    version="0.1.0",
    author="EchoLink Team",
    author_email="your.email@example.com",
    description="Client library for interacting with the EchoLink API service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/echolink-client",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "echolink-client=echolink_client:main",
        ],
    },
)


from setuptools import setup, find_packages

setup(
    name="docker-service-manager",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "blessed>=1.20.0",
        "docker>=7.1.0",
        "py-cui>=0.1.6",
        "tabulate>=0.9.0",
    ],
    entry_points={
        'console_scripts': [
            'docker-service-manager=docker_service_manager:main',
        ],
    },
    author="Replit User",
    description="A cross-platform Docker daemon control tool",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    keywords="docker, service, management, cross-platform",
    url="https://replit.com/@YOUR-USERNAME/docker-service-manager",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
)

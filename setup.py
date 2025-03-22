
from setuptools import setup, find_packages

setup(
    name="docker-service-manager",
    version="1.0.0",
    packages=find_packages(include=['docker_manager', 'docker_manager.*', 'docker_service_manager']),
    package_data={
        'docker_manager': ['templates/*.yaml', 'templates/*.json'],
    },
    install_requires=[
        "blessed>=1.20.0",
        "docker>=7.1.0",
        "matplotlib>=3.10.1",
        "psutil>=7.0.0",
        "py-cui>=0.1.6",
        "setuptools>=77.0.3",
        "tabulate>=0.9.0",
        "python-dateutil>=2.8.2",
    ],
    entry_points={
        'console_scripts': [
            'docker-service-manager=docker_service_manager:main',
            'dsm=docker_service_manager:main',
        ],
    },
    author="Replit User",
    author_email="your.email@example.com",
    description="A cross-platform Docker daemon control tool",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    keywords="docker, service, management, cross-platform, container, monitoring, health-report",
    url="https://github.com/your-username/docker-service-manager",
    project_urls={
        "Bug Tracker": "https://github.com/your-username/docker-service-manager/issues",
        "Documentation": "https://github.com/your-username/docker-service-manager#readme",
        "Source Code": "https://github.com/your-username/docker-service-manager",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.11",
    include_package_data=True,
)

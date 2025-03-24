from setuptools import setup, find_packages

setup(
    name="sevensense_device",  # Replace with your project's name
    version="1.0.0",  # Starting version
    author="Mattia Haas",  # Replace with your name
    packages=find_packages(),  # Automatically find all packages
    install_requires=["requests"],
)

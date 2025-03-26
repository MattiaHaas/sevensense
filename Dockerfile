# Use the official Ubuntu base image
FROM ubuntu:latest

# Specify running the RUN commands using bash
SHELL ["/bin/bash", "-c"]

# Set environment variables to non-interactive (to avoid prompts)
ENV DEBIAN_FRONTEND=noninteractive

# Update package lists and install Python
RUN apt-get update && \
    apt-get install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    && apt-get clean

# Clone the repository (replace with your repository URL)
RUN git clone -b improvements https://github.com/MattiaHaas/sevensense.git /app

# Set the working directory to the cloned repository
WORKDIR /app

# Create a Python virtual environment inside the repository directory and install pkgs
RUN python3 -m venv venv && \
    source venv/bin/activate && \
    python3 -m pip install -r requirements.txt

# Set environment variables (if needed for your script)
ENV DUT=A
ENV INITIAL_VERSION=2

# Set the default command to run python3
CMD ["/bin/bash", "-c", "source venv/bin/activate && coverage run -m pytest tests -v -s && coverage report -m"]

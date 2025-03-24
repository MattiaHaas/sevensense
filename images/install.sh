#!/bin/bash

# Function to display a progress bar
progress_bar() {
    local duration=$1  # Total time in seconds
    local bar_width=50  # Width of the progress bar (number of characters)

    # Loop over the duration
    for ((i = 1; i <= duration; i++)); do
        # Calculate how much of the bar should be filled
        progress=$((i * 100 / duration))
        completed=$((progress * bar_width / 100))
        remaining=$((bar_width - completed))

        # Build the progress bar string
        bar=$(printf "%${completed}s" "#" | tr " " "#")
        space=$(printf "%${remaining}s")

        # Print the progress bar with the percentage
        printf "\r[%-${bar_width}s] %d%%" "$bar$space" "$progress"
        sleep 1  # Simulate work being done (e.g., installation step)
    done
    echo  # Newline at the end
}

# Simulate the installation process
echo "Starting installation..."

# Simulate installation with a 10-second progress bar
progress_bar 10

echo "Installation complete!"

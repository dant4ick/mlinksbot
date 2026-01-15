#!/bin/bash

# Background updater: waits 24h, updates yt-dlp, then kills the bot (which restarts the loop)
update_loop() {
    while true; do
        sleep 86400
        echo "Updating yt-dlp..."
        pip install --upgrade yt-dlp
        echo "Restarting bot to apply update..."
        pkill -f "python main.py"
    done
}

# Start the updater in background
update_loop &

# Main loop: run the bot, restart if it exits
while true; do
    echo "Starting bot..."
    python main.py
    echo "Bot exited, restarting in 5 seconds..."
    sleep 5
done

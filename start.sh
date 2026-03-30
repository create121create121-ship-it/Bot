#!/bin/bash
# Start the bot in the background
python video_script_bot.py &
# Start the dashboard in the foreground (required for Render)
python dashboard.py

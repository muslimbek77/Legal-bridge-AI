#!/bin/bash
echo "Killing all celery processes for user $(whoami)..."
pkill -u $(whoami) -f "celery"
echo "Waiting for processes to exit..."
sleep 3
# Check if any remain and force kill
if pgrep -u $(whoami) -f "celery" > /dev/null; then
    echo "Force killing remaining processes..."
    pkill -9 -u $(whoami) -f "celery"
fi
echo "All celery processes killed."

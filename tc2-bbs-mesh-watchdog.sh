#!/bin/bash

CONTAINER_NAME="tc2-bbs-mesh"
ERROR_MSG="Broken pipe"
CHECK_INTERVAL=1m  # How often to check the logs (in seconds)

while true; do
  # Get logs from the last minute (or adjust as needed)
  if docker logs --since $CHECK_INTERVAL $CONTAINER_NAME 2>&1 | grep -q "$ERROR_MSG"; then
    echo "Error detected in logs: $ERROR_MSG. Restarting container..."
    docker restart $CONTAINER_NAME
    # Optional: Sleep for a few seconds to allow the container to restart
    sleep 120
  fi
  # Wait for the next check
  sleep 60
done

#!/bin/bash

# Start the Redis server in the background
redis-server --daemonize yes

# Start Daphne
# This will keep the container running
daphne -b 0.0.0.0 -p 8000 core.asgi:application

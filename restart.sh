#!/bin/bash

docker compose down
sleep 1
# Startup all the containers at once
docker compose up -d

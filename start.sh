#!/bin/bash

# Build the base images from which are based the Dockerfiles
# then Startup all the containers at once
docker build -t airflow-base docker/airflow
docker compose up -d --build

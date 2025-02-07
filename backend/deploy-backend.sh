#!/bin/bash

if [ ! -f .env ]; then
    echo ".env not found. Creation of .env file..."
    read -p "Please enter your HuggingFace Access Token: " user_token
    echo "HF_TOKEN=$user_token" > .env
    echo ".env file created successfully."
fi

read -p "Do you want to deploy in Docker (Y/N): " deploy_choice
deploy_choice=$(echo "$deploy_choice" | tr '[:upper:]' '[:lower:]')

if [ "$deploy_choice" = "y" ]; then
    if command -v nvidia-smi &> /dev/null; then
        echo "GPU detected. Using docker-compose-gpu.yml."
        docker-compose -f docker-compose-gpu.yml up --build
    else
        echo "No GPU detected. Using docker-compose-cpu.yml."
        docker-compose -f docker-compose-cpu.yml up --build
    fi
elif [ "$deploy_choice" = "n" ]; then
    echo "Deployment without Docker: direct launch of App.py."
    python src/App.py
else
    echo "Invalid choice. Please answer with Y or N."
    exit 1
fi
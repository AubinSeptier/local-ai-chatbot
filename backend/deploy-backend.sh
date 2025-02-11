#!/bin/bash

if [ ! -f .env ]; then
    echo ".env not found. Creation of .env file..."
    read -sp "Please enter your HuggingFace Access Token: " hf_token
    echo
    read -sp "Please enter your OpenAI API Key: " openai_token
    echo
    echo "HF_TOKEN=$hf_token" > .env
    echo "OPENAI_API_KEY=$openai_token" >> .env
    echo ".env file created successfully."
else
    if ! grep -q "^HF_TOKEN=" .env; then
        read -sp "Please enter your HuggingFace Access Token to add to .env file: " hf_token
        echo
        echo "HF_TOKEN=$hf_token" >> .env
        echo "HF_TOKEN added to .env file."
    fi

    if ! grep -q "^OPENAI_API_KEY=" .env; then
        read -sp "Please enter your OpenAI API Key to add to .env file: " openai_token
        echo
        echo "OPENAI_API_KEY=$openai_token" >> .env
        echo "OPENAI_API_KEY added to .env file."
    fi
fi

if [ -f /.dockerenv ]; then
    echo "Already in a Docker container. Launching app.py..."
    python src/App.py
    exit 0
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
# Backend

This folder contains the backend of the project.

## Architecture

The backend is organized as follows :

* `src/`: contains the source code of the backend.
* `models/`: folder to store the models used by the backend.
* `requirements.txt`: list of Python packages required to run the backend.
* `deploy-backend.sh`: bash script to deploy the backend.
* `Dockerfile`: Dockerfile to build the Docker image of the backend.
* `docker-compose-cpu.yml`: Docker Compose file to deploy the backend on CPU.
* `docker-compose-gpu.yml`: Docker Compose file to deploy the backend on GPU.

Once the backend is deployed, there are one new file and one new folder :

* `instance/`: folder to store the SQLite database.
* `.env`: file to store the environment variables (HuggingFace access token and OpenAI API key).

## Code structure

In the `src/` folder, the code is organized as follows :

* `app.py` : Database initialization, choice of model parameters, Flask launch.
* `ChatApi.py` : Orchestration of the entire chatbot (conversation management, etc.).
* `ChatModel.py` : Customized model implementation, supporting token streaming.
* `Conversation.py` : Conversation history management.
* `Database.py` : SQLite interface (conversation storage, etc.).
* `ModelManager.py` : Download and load models locally.
* `routes.py` : Management of Flask routes and frontend/backend communication.
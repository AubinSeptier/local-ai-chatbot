# Local AI Chatbot 

## Introduction

The aim of this project is to develop an **intelligent chatbot** for the **Université du Québec à Chicoutimi (UQAC)**, capable of answering employees' questions about the **university's management manual**. Using the **Retrieval Augmented Generation (RAG)** technique, the chatbot extracts and synthesizes relevant information from a large set of documents, including HTML pages and PDF files.

🐋Docker images of the backend are available [here](https://hub.docker.com/repository/docker/aubinseptier/local-ai-chatbot/general).

## ⚙️Technologies and tools

The chatbot is built using the following technologies and tools :

* [LangChain](https://www.langchain.com)
* [HuggingFace Transformers](https://huggingface.co/docs/transformers/index)
* [Models from HuggingFace](https://huggingface.co)
* [OpenAI Embedding](https://python.langchain.com/docs/integrations/text_embedding/openai/)
* [Chroma DB](https://www.trychroma.com)
* [Flask](https://flask.palletsprojects.com/en/stable/)
* [React](https://react.dev)
* [SQLite](https://www.sqlite.org)


## ⚒️Installation

⚠️**Prerequisites**: You need to have Docker installed on your machine to deploy the backend in a container. If you don't have it, you can download it [here](https://www.docker.com/products/docker-desktop/). You also need to have Node.js installed to run the frontend. If you don't have it, you can download it [here](https://nodejs.org/en/download/).

Here's a step-by-step guide to installing the chatbot on your local machine :

1. Clone the repository to your local machine using the following command:

```bash
git clone https://github.com/AubinSeptier/local-ai-chatbot.git
```

2. Go to [huggingface.co](https://huggingface.co), create or log in to your account and generate an access token (keep it for later).  
ℹ️**Note**: To access to Llama models, you'll need to accept the terms and conditions on the specific model page on HuggingFace.

3. Go to [openai.com](https://platform.openai.com/), create or log in to your account and generate an API Key (keep it for later).  
ℹ️**Note**: An OpenAI API Key is required to use the RAG functionality in the chatbot. OpenAI API key is not free and you may need to pay for it.

4. Open the `backend` folder in a terminal and launch the bash script `deploy-backend.sh`:

```bash
bash deploy-backend.sh
```

5. Paste the HuggingFace access token and the OpenAI API Key you generated earlier when asked. Then choose if you want to deploy the chatbot in a Docker container or not (if you choose not to, you'll have to install the `requirements.txt` manually before).  
Then, the script will build the container and launch the app via Docker (port: 7860) or directly on your machine.  
ℹ️**Note**: To configure Docker Dekstop on Windows (WSL2) to use GPU acceleration, you can follow the instructions [here](https://docs.docker.com/desktop/features/gpu/).

6. Open the `frontend/my-chatbot-frontend` folder in another terminal and execute the following commands:

```bash
npm upgrade 
npm run dev
```

7. Open your web browser and go to `http://localhost:5173` to access the chatbot.

8. You can restart the server at any time by running the following command in the `backend` folder:

```bash
bash deploy-backend.sh
```  

ℹ️**Note**: To restart it in the previously built Docker container, please run the script from the container.


## 🛠️Configuration

Here are some configuration options you can change in the `backend/src/app.py` file :

```python	
    generation_config = {
        "max_new_tokens": 1024,
        "temperature": 0.7,
        "top_k": 50,
        "top_p": 0.95
        "do_sample": True
        # ... other generation parameters
    }

    chat_api = ChatAPI(
        model_name="meta-llama/Llama-3.2-1B-Instruct",
        generation_config=generation_config,
        max_history=100,
        system_prompt="You are a helpful assistant.",
        db=db
    )
```

* You can change generation config (temperature, max_new_tokens, etc.) to adjust the chatbot's responses.

* You can change the `model_name` variable to use another model from HuggingFace. Just copy the model name from the model's page URL on HuggingFace (e.g. `meta-llama/Llama-3.2-3B-Instruct`). 

* You can change the `system_prompt` to define the chatbot's role.

* In the `backend/models` folder, you can see and manage all downloaded models available for the chatbot.    

ℹ️**Note**: If you want to change the configuration or the model used by the chatbot, you'll need to restart the backend server to apply the changes. Don't need to rebuild the Docker container, just restart the server from the container or your machine depending if you used Docker or not.


## 📅What's next ?

This project is still in development and many improvements can be made. Here are some ideas for future updates :

* Download and load the desired LLM from the web interface.

* Modify LLM configuration directly from the web interface.

* Improving RAG performance.

* To be able to choose whether or not to use RAG.

* Retain the user's theme preference (Light/Dark).

* Integrate query_data.py directly into the Conversation class.
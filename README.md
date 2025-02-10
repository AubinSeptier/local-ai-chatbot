# Local AI Chatbot 

## Introduction



## Installation

⚠️ **Prerequisites**: You need to have Docker installed on your machine to deploy the backend in a container. If you don't have it, you can download it [here](https://www.docker.com/products/docker-desktop/). You also need to have Node.js installed to run the frontend. If you don't have it, you can download it [here](https://nodejs.org/en/download/).

Here's a step-by-step guide to installing the chatbot on your local machine.

1. Clone the repository to your local machine using the following command:

```bash
git clone https://github.com/AubinSeptier/local-ai-chatbot.git
```

2. Go to [huggingface.co](https://huggingface.co), create or log in to your account and generate an access token (keep it for later).
ℹ️ **Note**: To access to Llama models, you'll need to accept the terms and conditions on the specific model page on HuggingFace.

3. Go to [openai.com](https://platform.openai.com/), create or log in to your account and generate an API Key (keep it for later).
ℹ️ **Note**: An OpenAI API Key is required to use the RAG functionality in the chatbot. OpenAI API key is not free and you may need to pay for it.

4. Open the `backend` folder in a terminal and launch the bash script `deploy-backend.sh`:

```bash
bash deploy-backend.sh
```

5. Paste the HuggingFace access token and the OpenAI API Key you generated earlier when asked. Then choose if you want to deploy the chatbot in a Docker container or not (if you choose not to, you'll have to install the `requirements.txt` manually before).  
Then, the script will build the container and launch the app via Docker (port: 7860) or directly on your machine.  
ℹ️ **Note**: To configure Docker Dekstop on Windows (WSL2) to use GPU acceleration, you can follow the instructions [here](https://docs.docker.com/desktop/features/gpu/).

6. Open the `frontend/my-chatbot-frontend` folder in another terminal and execute the following commands:

```bash
npm upgrade 
npm run dev
```

7. Open your browser and go to `http://localhost:5173` to access the chatbot.


## Configuration

Here some configuration options you can change in the `backend/src/app.py` file:

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

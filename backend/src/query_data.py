"""
Our objective here is to find the chinks in our database that
will most likely contain the answer to the question we want to ask
"""
"""
we re gonna take a query and turn that into an embedding using the same function
scan throu the database and find the chunks of information that are closest in embedding distance to our query
"""

import argparse
# from dataclasses import dataclass
from langchain_community.vectorstores import Chroma

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
load_dotenv()
from langchain.embeddings import OpenAIEmbeddings
import os 

embeddings = OpenAIEmbeddings(openai_api_key=os.environ.get("OPENAI_API_KEY"))



CHROMA_PATH = "chroma"
DATA_PATH ='documents/mock_data'

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""


def query_rag(query_text: str) -> str:
    # Create CLI.
    #parser = argparse.ArgumentParser()
    #parser.add_argument("query_text", type=str, help="The query text.")
    #args = parser.parse_args()
    #query_text = args.query_text
    """
    ici c important pour nous d utiliser la nene embedding functiom
    that we uses un creating our data
    """
    # Prepare the DB.
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    """
    Once the data base is loaded on peut chercher the chunk
    that best matches our query by passing our query as an argument
    and then specify the number of results we want to retrieve
    the result of the search will be a list of tuples where each tuple contains
    a doument and it s relevance score
    """
    


    # Search the DB.
    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    """
    before processinf the result we can add here checks 
    """
    
    if len(results) == 0 or results[0][1] < 0.7:
        print(f"Unable to find matching results.")
        return

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    return context_text  # Return the retrieved context
    # Build prompt using a template
    # prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    # prompt = prompt_template.format(context=context_text, question=query_text)
    # print(prompt)

    """
    here we need to all the model that aubin and theo worked on

    """
    # model = ChatOpenAI(openai_api_key=os.environ.get("OPENAI_API_KEY"))
    # response_text = model.predict(prompt)

    # sources = [doc.metadata.get("source", None) for doc, _score in results]
    # formatted_response = f"Response: {response_text}\nSources: {sources}"
    # print(formatted_response)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    output = query_rag(args.query_text)
    print(output)
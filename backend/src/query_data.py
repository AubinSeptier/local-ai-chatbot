"""
Our objective here is to find the chinks in our database that
will most likely contain the answer to the question we want to ask
"""
"""
we re gonna take a query and turn that into an embedding using the same function
scan throu the database and find the chunks of information that are closest in embedding distance to our query
"""

import argparse
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import os 
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MyAppLogger")

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable required")
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)



CHROMA_PATH = "./chroma"
DOCUMENT_PATH = "./documents/uqac_data.md"  

if not os.path.exists(DOCUMENT_PATH):
    print(f" ERROR: The file {DOCUMENT_PATH} does not exist! Check your path.")
else:
    print(f" Found UQAC document at {DOCUMENT_PATH}")
    with open(DOCUMENT_PATH, "r", encoding="utf-8") as f:
        data = f.read()
        print(" File Preview:\n", data[:500])  # Print first 500 characters

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""


def query_rag(query_text: str) -> str:
    """Retrieve relevant context and return document sources."""
    
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Vérifier si la base contient des documents
    num_docs = db._collection.count()
    print(f" ChromaDB contient {num_docs} documents stockés.")

    # Effectuer une recherche des documents pertinents
    results = db.similarity_search_with_relevance_scores(query_text, k=5)

    # Vérifier si des résultats pertinents ont été trouvés
    if not results or results[0][1] < 0.7:
        print(f" Aucun document pertinent trouvé pour la requête : {query_text}")
        return "Je suis désolé, mais je n'ai pas trouvé d'information pertinente dans les documents fournis."

    print(f" {len(results)} résultats pertinents trouvés pour la requête.")

    # Extraire le contenu et les sources des résultats
    context_texts = []
    sources = set()  # Use a set to avoid duplicate sources

    for doc, score in results:
        logger.info(f"Document Score: {score} - Snippet: {doc.page_content[:100]}...")
        context_texts.append(doc.page_content.strip())  # Ajouter le texte du document
        source = doc.metadata.get("source", "Source inconnue")
        if source not in sources:  # Ensure each source is unique
            sources.add(source)

    # Formater la réponse avec les sources visibles
    context_text = "\n\n---\n\n".join(context_texts)
    sources_text = "\n".join([f"- [{source}]({source})" for source in sources])  # Format sources as Markdown links



    return f"{context_text}\n\n**Sources**:\n{sources_text}"









if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    output = query_rag(args.query_text)
    print(output)
# from langchain.document_loaders import DirectoryLoader
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.embeddings import OpenAIEmbeddings
#from langchain_openai import OpenAIEmbeddings


from langchain_community.vectorstores import Chroma
import openai 
from dotenv import load_dotenv
import os
import shutil 

import nltk
nltk.download('averaged_perceptron_tagger_eng')

load_dotenv()
from langchain.embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(openai_api_key=os.environ.get("OPENAI_API_KEY"))




CHROMA_PATH = "chroma"
DATA_PATH ='documents/mock_data'


def main():
    generate_data_store()


def generate_data_store():
    documents = load_documents()
    chunks = split_text(documents)
    save_to_chroma(chunks)

"""
loading files in documetns and turning them into smtg called documents
the document will contain the content of the file as well as some information like the source file if we have multiple files 

"""

def load_documents():
    loader=DirectoryLoader(DATA_PATH, glob='*.md')
    documents = loader.load()
    return documents

"""
We have to split our markdown file into chuncks 
pour fire cela we use a recursive character text splitter
we can set the chunk size, nbr of character and overlap between each chunk
"""

def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    document = chunks[10]
    print(document.page_content)
    print(document.metadata)

    return chunks

"""
We re gonna be using chromaDB to turn our chuncks into a database 
that uses vector embeddings as the key 
"""

def save_to_chroma(chunks: list[Document]):
    # Clear out the database first.
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    # Create a new DB from the documents.
    db = Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_PATH)

    db.persist()
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")

"""
At this point normally we have our vector data base created and we re ready to 
use it 
"""


if __name__ == "__main__":
    main()
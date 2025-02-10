import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
from langchain.schema import Document  

load_dotenv()

#CHECK LATER
DOCUMENT_PATH = "./documents"
CHROMA_PATH = "./chroma"
os.makedirs(DOCUMENT_PATH, exist_ok=True)
os.makedirs(CHROMA_PATH, exist_ok=True)

# User-Agent to avoid blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Allowed domain
BASE_URL = "https://www.uqac.ca/mgestion/"

# File types to ignore
IGNORED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".mp4", ".avi", ".zip", ".rar", ".exe"}

# Track downloaded PDFs to avoid duplicates
downloaded_pdfs = set()

def download_pdf(url, folder="./documents/pdfs"):
    """Downloads a PDF file and stores it locally."""
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, os.path.basename(urlparse(url).path))

    if filename in downloaded_pdfs:
        print(f"Skipping duplicate PDF: {filename}")
        return None

    try:
        response = requests.get(url, headers=HEADERS, stream=True, timeout=10)
        response.raise_for_status()
        with open(filename, "wb") as f:
            f.write(response.content)
        downloaded_pdfs.add(filename)
        print(f" PDF downloaded: {filename}")
        return filename
    except requests.exceptions.RequestException as e:
        print(f" PDF Download Error {url}: {e}")
        return None

def scrape_website(start_url, visited=None):
    """Scrapes UQAC website and extracts text + PDFs."""
    if visited is None:
        visited = set()

    to_visit = [start_url]
    docs = []

    while to_visit:
        url = to_visit.pop()
        if url in visited:
            continue
        visited.add(url)

        print(f"🔍 Scraping: {url}")
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f" Request error: {e}")
            continue

        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            print(f" Skipping non-HTML: {url} [{content_type}]")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        entry_headers = soup.find_all("div", class_="entry-header")
        entry_contents = soup.find_all("div", class_="entry-content")
        text = "\n".join([div.get_text() for div in entry_headers + entry_contents])

        if text.strip():
            docs.append((url, text))

        # Extract links and find PDFs
        for link in soup.find_all("a", href=True):
            href = urljoin(url, link["href"])
            parsed_href = urlparse(href)

            if not href.startswith(BASE_URL):
                continue

            if any(parsed_href.path.lower().endswith(ext) for ext in IGNORED_EXTENSIONS):
                print(f"⚠️ Skipping unsupported file: {href}")
                continue

            if parsed_href.netloc == urlparse(start_url).netloc and href not in visited:
                if href.endswith(".pdf"):
                    pdf_path = download_pdf(href)
                    if pdf_path:
                        docs.append((href, pdf_path))
                else:
                    to_visit.append(href)

        # Limit to 100 documents
        if len(docs) > 100:
            break

    return docs

def process_documents(docs):
    """Processes extracted text and PDF documents."""
    loaded_docs = []
    for url, content in docs:
        if content.endswith(".pdf"):
            try:
                pdf_loader = PyPDFLoader(content)
                pdf_docs = pdf_loader.load()
                for doc in pdf_docs:
                    loaded_docs.append({"text": doc.page_content, "source": url})
            except Exception as e:
                print(f" PDF Read Error ({content}): {e}")
        else:
            loaded_docs.append({"text": content, "source": url})

    print(f" Total documents processed: {len(loaded_docs)}")

    # Save as Markdown
    output_file = os.path.join(DOCUMENT_PATH, "uqac_data.md")
    with open(output_file, "w", encoding="utf-8") as f:
        for doc in loaded_docs:
            f.write(f"## Source: {doc['source']}\n\n")
            f.write(f"{doc['text']}\n\n---\n\n")

    print(f" Processed documents saved to {output_file}")

    return loaded_docs  # Return processed documents for indexing

def create_chroma_db(processed_docs):
    """Creates and stores processed documents in ChromaDB."""

    # Delete previous ChromaDB
    if os.path.exists(CHROMA_PATH):
        print(f"🗑 Deleting old ChromaDB at {CHROMA_PATH}...")
        os.system(f"rm -rf {CHROMA_PATH}")

    # Convert dicts into LangChain Document objects
    documents = []
    for doc in processed_docs:
        source = doc.get("source", "Unknown")  # Ensure source exists
        text = doc.get("text", "").strip()

        if text:  # Avoid storing empty documents
            documents.append(Document(page_content=text, metadata={"source": source}))
            print(f" Storing Document: {text[:100]}... | Source: {source}")  # Debug print

    if not documents:
        print(" No valid documents found to store in ChromaDB!")
        return

    # Initialize OpenAI Embeddings (Fix deprecation warning)
    embedding_function = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))

    # Store documents in ChromaDB
    vectorstore = Chroma.from_documents(documents, embedding_function, persist_directory=CHROMA_PATH)

    print(f" ChromaDB successfully created at {CHROMA_PATH} with {len(documents)} documents.")




if __name__ == "__main__":
    # Step 1: Scrape website
    scraped_docs = scrape_website(BASE_URL)

    # Step 2: Process and structure documents
    processed_docs = process_documents(scraped_docs)

    # Step 3: Save documents & metadata
    metadata_file = os.path.join(DOCUMENT_PATH, "uqac_metadata.txt")
    with open(metadata_file, "w", encoding="utf-8") as f:
        f.write(f"Total documents processed: {len(processed_docs)}\n")
        f.write(f"Example document: {processed_docs[0]}\n")

    print(f" Metadata saved to {metadata_file}")

    # Step 4: Create ChromaDB
    create_chroma_db(processed_docs)

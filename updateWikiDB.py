from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from tqdm import tqdm
import os

dataPath = "nbaBIO"
chromaPath = "chroma"

# Load existing Chroma DB
embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)

db = Chroma(
    embedding_function=embedding,
    persist_directory=chromaPath
)

# List already indexed files using metadata (if tracked), or fallback to manual tracking
indexed_files_path = os.path.join(chromaPath, "indexed_files.txt")
indexed_files = set()

if os.path.exists(indexed_files_path):
    with open(indexed_files_path, "r") as f:
        indexed_files = set(f.read().splitlines())

# Detect new files
all_files = [f for f in os.listdir(dataPath) if os.path.isfile(os.path.join(dataPath, f))]
new_files = [f for f in all_files if f not in indexed_files]

# Process new documents
documents = []
for file in tqdm(new_files, desc="Loading new documents"):
    path = os.path.join(dataPath, file)
    try:
        loader = TextLoader(path, encoding="utf-8")
        documents.extend(loader.load())
    except Exception as e:
        print(f"Skipping {file}: {e}")

# Split and index
if documents:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=500,
        length_function=len,
        add_start_index=True
    )
    chunks = []
    for doc in tqdm(documents, desc="Splitting new documents"):
        chunks.extend(text_splitter.split_documents([doc]))

    for chunk in tqdm(chunks, desc="Adding new chunks to Chroma"):
        db.add_documents([chunk])

    db.persist()

    # Update file tracker
    with open(indexed_files_path, "a") as f:
        for file in new_files:
            f.write(file + "\n")

    print(f"Added {len(new_files)} new files and {len(chunks)} chunks to `{chromaPath}`.")
else:
    print("No new documents found. You're all caught up!")
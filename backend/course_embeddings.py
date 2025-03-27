from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Index as PineconeIndex
import json
import os
import time
import pinecone
from pinecone import ServerlessSpec
from dotenv import load_dotenv
from tqdm import tqdm
from langchain_community.vectorstores import Pinecone as LangchainPinecone

load_dotenv()

BATCH_SIZE = 100

pc = pinecone.Pinecone(api_key=os.getenv("PINECONE_API_KEY"), environment="us-east-1")
index_name = "explorecourses-cs"

embedding_fn = HuggingFaceEmbeddings(
    model_name="intfloat/e5-large-v2",
    model_kwargs={
        'device': 'cpu'
    },
    encode_kwargs={
        'normalize_embeddings': True
    }
)

JSON_FILE = os.path.join("data", "scraped", "courses_cs_all.json")
all_courses = []
with open(JSON_FILE, "r") as f:
    all_courses = json.load(f)

all_courses = all_courses[:50]

def get_embedding(description):
    return embedding_fn.embed_query(description)

def initialize_index():
    existing_indexes = pc.list_indexes().names()
    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)
    time.sleep(1)
    index = pc.Index(index_name)
    print(f"✨initialized index!")
    print(index.describe_index_stats())
    return index

def embed_courses(courses):
    course_description = [course["courseDescription"] for course in courses]
    course_embeddings = embedding_fn.embed_documents(course_description)
    pinecone_vectors = [
        {
            "id": f"doc-{i}",
            "values": embedding,
            "metadata": {}
        }
        for i, embedding in tqdm(list(enumerate(course_embeddings)), desc="😎embedding courses")
    ]
    print(f"✨created pinecone vectors: {len(pinecone_vectors)}")
    return pinecone_vectors

def upsert_to_index(index, pinecone_vectors, mode="all", batch_size=BATCH_SIZE):
    if mode == "batch":
        for i in tqdm(range(0, len(pinecone_vectors), batch_size)):
            batch = pinecone_vectors[i:i+batch_size]
            index.upsert(batch)
            print(f"✨added batch: {i}")
    else:
        index.upsert(pinecone_vectors)
    print(f"✨added all {len(pinecone_vectors)} vectors to pinecone!\n")
    print(index.describe_index_stats())

def add_to_database(clear):
    index = initialize_index()
    pinecone_vectors = embed_courses(all_courses)
    upsert_to_index(index, pinecone_vectors, mode="batch")
    return index, pinecone_vectors

def setup_retrieval(index):
    text_field = "description"
    raw_index = pc.Index(index_name)  # this is the v3 Pinecone index
    vectorstore = LangchainPinecone(
        index=raw_index,
        embedding=embedding_fn,
        text_key=text_field
    )
    return vectorstore

def get_similar_courses(course, vectorstore):
    similar_courses = vectorstore.similarity_search(course["courseDescription"], 5)
    print(f"Course: {course['title']}\n")
    for course in similar_courses:
        print(f"- {course.metadata.get('title', 'No title')}")
    return similar_courses

if __name__ == "__main__":
    index, pinecone_vectors = add_to_database(clear=True)
    vectorstore = setup_retrieval(index)
    get_similar_courses(all_courses[100], vectorstore)

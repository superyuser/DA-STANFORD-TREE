import json
import psycopg2
from psycopg2.extras import execute_batch  # for efficient bulk operations
import os
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel

JSON_FILE = r"C:\Users\Bubble\Desktop\001 Blockchain\edulink\scrapers\Stanford\data\scraped\AllDepts_Got55.json"

DB_PARAMS = {
    'dbname': 'edulink',
    'user': 'postgres',
    'password': '',
    'host': 'localhost',
    'port': '5432'
}

# Initialize the embedding model (using SentenceTransformer all-MiniLM-L6-v2)
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
embedding_tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)
embedding_model = AutoModel.from_pretrained(EMBEDDING_MODEL_NAME)

def compute_embedding(text: str) -> list:
    """Compute vector embedding for the given text using mean pooling."""
    if not text:
        text = ""
    inputs = embedding_tokenizer.encode_plus(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = embedding_model(**inputs)
    # Mean pooling over token embeddings
    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().tolist()
    return embedding

def createTables():
    commands = [
        # Drop tables in order using CASCADE to remove dependencies
        "DROP TABLE IF EXISTS courses CASCADE;",
        "DROP TABLE IF EXISTS departments CASCADE;",
        "DROP TABLE IF EXISTS schools CASCADE;",
        
        # Create departments table
        """
        CREATE TABLE IF NOT EXISTS departments (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE,
            code VARCHAR(50) UNIQUE NOT NULL
        )
        """,
        # Create courses table with an 'embedding' column as JSONB
        """
        CREATE TABLE IF NOT EXISTS courses (
            id SERIAL PRIMARY KEY,
            department_id INTEGER REFERENCES departments(id),
            course_code VARCHAR(50) UNIQUE NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            instructors TEXT[],
            credits INTEGER,
            ipfs_materials_hash TEXT,
            blockchain_certificate_id bytea,
            embedding jsonb,
            UNIQUE(department_id, course_code)
        )
        """
    ]

    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        for command in commands:
            cur.execute(command)
        conn.commit()
        cur.close()
        print("[CREATED TABLES] Successfully created tables!")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
    finally:
        if conn is not None:
            conn.close()

def updateSchema():
    """
    Update the courses table schema by adding the 'embedding' column if it doesn't exist.
    This is useful when the table already exists from a previous run.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        # Add the embedding column as JSONB if it does not exist
        cur.execute("ALTER TABLE courses ADD COLUMN IF NOT EXISTS embedding jsonb;")
        conn.commit()
        cur.close()
        print("[UPDATED SCHEMA] courses table updated with embedding column!")
    except Exception as e:
        print("Error updating schema:", e)
    finally:
        if conn is not None:
            conn.close()

def storeCourses(file=JSON_FILE):
    with open(file, "r") as f:
        courses = json.load(f)

    conn = None

    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        for course in courses:
            # Derive department code from the course number
            dept_code = course['courseNumber'].split()[0]
            
            # Try to get department id; if not found, insert a new department
            cur.execute("SELECT id FROM departments WHERE code = %s", (dept_code,))
            dept_result = cur.fetchone()
            if dept_result is None:
                cur.execute(
                    "INSERT INTO departments (name, code) VALUES (%s, %s) RETURNING id", 
                    (dept_code, dept_code)
                )
                dept_row = cur.fetchone()
                if dept_row is None:
                    print(f"Failed to insert department: {dept_code}")
                    continue  # Skip this course if department insertion fails
                dept_id = dept_row[0]
            else:
                dept_id = dept_result[0]
            
            # Compute the embedding for the course description
            embedding_vector = compute_embedding(course['courseDescription'])
            
            # Insert course into the courses table, including the embedding as JSON
            cur.execute(
                """
                INSERT INTO courses (department_id, course_code, title, description, instructors, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (course_code) DO NOTHING
                RETURNING id
                """,
                (dept_id, course['courseNumber'], course['courseName'], course['courseDescription'], course['instructors'], json.dumps(embedding_vector))
            )

            # Check if insertion was successful
            course_row = cur.fetchone()
            if course_row is None:
                print(f"[DUPLICATE or SKIPPED]: {course['courseNumber']} already exists or was not inserted.")
            else:
                course_id = course_row[0]
                print(f"[STORED COURSE]: {course['courseNumber']} stored with id {course_id}")
            
            # Commit after each course (or consider batching for efficiency)
            conn.commit()
        
        print("[STORED COURSES] Successfully stored courses!")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
        if conn:
            conn.rollback()  # rollback in case of error
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    createTables()
    updateSchema()
    storeCourses()
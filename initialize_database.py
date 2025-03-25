from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()

DB_PARAMS = {
    'dbname': os.getenv("DB_NAME"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'host': os.getenv("DB_HOST"),
    'port': os.getenv("DB_PORT")
}

def create_tables():
    commands = [
        """DROP TABLE IF EXISTS courses CASCADE;""",
        """DROP TABLE IF EXISTS prereqs CASCADE;""",
        """
        CREATE TABLE IF NOT EXISTS courses (
            id SERIAL PRIMARY KEY,
            code VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS prereqs (
            id SERIAL PRIMARY KEY,
            course_id INT NOT NULL,
            prereq_id INT NOT NULL,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
            FOREIGN KEY (prereq_id) REFERENCES courses(id) ON DELETE CASCADE,
            UNIQUE (course_id, prereq_id)
        )
        """
    ] # unique (course_id, prereq_id) allows only one conn per course_id, prereq_id pair!

    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        for command in commands:
            cur.execute(command)
        conn.commit()
        cur.close()
        print("🤗💌🤗successfully created tables heheh!")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
    finally:
        if conn is not None:
            conn.close()

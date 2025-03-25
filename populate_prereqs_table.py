from initialize_database import DB_PARAMS
from add_prerequisites import get_course_id
from psycopg2.extras import execute_batch
import psycopg2
import json
import time

JSON_FILE = r"data\scraped\prereqs.json"

with psycopg2.connect(**DB_PARAMS) as conn:
    with conn.cursor() as curr:
        curr.execute("DROP TABLE IF EXISTS prereqs CASCADE;")
        curr.execute("""
        CREATE TABLE IF NOT EXISTS prereqs (
            id SERIAL PRIMARY KEY,
            course_id INT NOT NULL,
            prereq_id INT NOT NULL,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
            FOREIGN KEY (prereq_id) REFERENCES courses(id) ON DELETE CASCADE,
            UNIQUE (course_id, prereq_id)
        )
        """)
        conn.commit()
        insert_pairs = []
        with open(JSON_FILE, "r") as f:
            data = json.load(f)
            for course in data:
                course_id = get_course_id(course["courseNumber"], curr)
                for prereq in course["prerequisites"]:
                    prereq_id = get_course_id(prereq, curr)
                    if prereq_id and course_id:
                        insert_pairs.append((course_id, prereq_id))
                    else:
                        print(f"❌Prerequisite {prereq} not found for course {course['courseNumber']}")

            print(f"💾 Inserting {len(insert_pairs)} prerequisite links...")
            execute_batch(curr, """
            INSERT INTO prereqs (course_id, prereq_id) 
            VALUES (%s, %s)
            ON CONFLICT (course_id, prereq_id) DO NOTHING;
            """, insert_pairs)
            conn.commit()
            time.sleep(0.1)
            # print(f"✅successfully processed {course['courseNumber']}!")
            num_courses = len(data)
            print(f"🎯🎯🎯Finished inserting {num_courses} courses!")

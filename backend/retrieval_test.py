from initialize_database import DB_PARAMS
from add_prerequisites import get_course_id
from psycopg2.extras import execute_batch
import psycopg2
import json
import time

# brief cli viz
with psycopg2.connect(**DB_PARAMS) as conn:
    with conn.cursor() as curr:
        command = """
        SELECT c.code AS course_node, c.name AS course_name, p.code AS prereq_code, p.name AS prereq_name
        FROM prereqs
        JOIN courses c ON prereqs.course_id = c.id
        JOIN courses p ON prereqs.prereq_id = p.id
        LIMIT 10;
        """
        curr.execute(command)
        results = curr.fetchall()
        for row in results:
            course_code, course_name, prereq_code, prereq_name = row
            print(f"Course: {course_code} -> Prereq: {prereq_code}")
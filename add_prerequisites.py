from ollama import chat
from tqdm import tqdm
from initialize_database import create_tables, DB_PARAMS
import psycopg2
import json
import re
import time

# performs baby checks of dataset

JSON_FILE = "data\scraped\courses_cs_all.json"
PROMPT_TEMPLATE = """
You are a course advisor for Stanford University. You will be given a course description. Your task is to extract the **prerequisites** and return them as a **JSON list**, like this:

["CS 106A", "CS 107", "Linear Algebra"]

Only return the JSON list and nothing else — no explanations, no formatting, no labels.

Follow these rules in order of priority:

1. **If specific course numbers are listed as prerequisites**, extract all of them in the format "SUBJECT CODE" (e.g., "CS 106A"). 
   - Add a space between the subject and number (e.g., "CS106A" → "CS 106A").
   - Include all course codes explicitly listed in the text, even if they’re in parentheses or embedded in sentences.
   - Always include the full course code with both subject and number, even if only the number is mentioned in the text. For example, if "193P" is listed and the course is in the CS department, return "CS 193P".
   - The current course is from the {subject} department. Use this subject for any course numbers that are missing one.

2. **If there are no course numbers**, extract **clear verbal prerequisite descriptions** (e.g., "Linear Algebra", "Introductory Biology").
   - Exclude vague or general phrases like "mathematical maturity", "strong programming skills", or "background in statistics".
   - Always exclude "consent of instructor" and any similar phrases.

3. If **no prerequisites are mentioned**, return an empty list: `[]`.

Now, analyze the following course description and return the JSON list only:

{courseDescription}
"""

def get_all_courses():
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
        return [entry["courseNumber"] for entry in data]

def generate_prompt(subject, courseDescription):
    return PROMPT_TEMPLATE.format(subject=subject, courseDescription=courseDescription)

def clean_course_codes(result):
    pattern = re.compile(r"[A-Z]{2,}\s?\d{1,4}[A-Z]?")
    cleaned_results = []
    for code in result:
        cleaned_results.extend(re.findall(pattern, code.strip()))
    # print(f"✨Cleaned codes: {cleaned_results}")
    return cleaned_results

def normalize_course_codes(result):
    pattern = re.compile(r"([A-Z]{2,})\s?(\d{1,4})([A-Z]?)")
    normalized_results = []
    for course in result:
        match = pattern.match(course)
        if match:
            course_num, course_title, course_letter = match.groups()
            normalized_results.append(f"{course_num} {course_title}{course_letter}")
    # print(f"✨Normalized codes: {normalized_results}")
    return normalized_results

def process_pres(result, valid_courses):
    just_codes = clean_course_codes(result)
    normalize_codes = normalize_course_codes(just_codes)
    valid_codes = [code for code in normalize_codes if code in set(valid_courses)]
    # print(f"✨Matching valid codes: {valid_codes}")
    invalid_codes_to_print = [code for code in normalize_codes if code not in valid_courses]
    # print(f"💔Invalid codes: {invalid_codes_to_print}")
    return valid_codes

def get_course_id(code, curr):
    curr.execute("SELECT id FROM courses WHERE code = %s", (code,))
    result = curr.fetchone()
    return result[0] if result else None

def main():
    print(f"➡️Loading all courses...")
    valid_courses = get_all_courses()

    print(f"➡️Initializing database...")
    create_tables()

    all_courses = []
    with open("data\scraped\courses_cs_all.json", "r") as f:
        data = json.load(f)
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as curr:
                # two-pass #1: insert all courses
                for course in tqdm(data):
                    curr.execute("""
                    INSERT INTO courses (code, name, description)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (code) DO NOTHING
                    """, (course["courseNumber"], course["courseName"], course["courseDescription"]))
                
                print(f"🌬️🌬️🌬️ Done inserting courses.")
                # pass #2: populate prereqs
                for course in tqdm(data[:100], leave=False):
                    course_obj = course
                    # get prereqs (ollama -> clean -> process)
                    messages = [
                        {
                            "role": "user",
                            "content": generate_prompt(course["courseNumber"].split(" ")[0], course["courseDescription"])
                        }
                    ]

                    response = chat("llama3.2", messages)
                    try:
                        raw_result = json.loads(response["message"]["content"])
                    except json.JSONDecodeError:
                        print(f"❌Failed to parse JSON response for {course['courseNumber']}\nRaw result: {response['message']['content']}\n")
                        raw_result = response["message"]["content"]
                    time.sleep(0.05)
                    course_obj["prerequisites"] = process_pres(raw_result, valid_courses)
                    # print(f"📘 {course_obj['courseNumber']} → {course_obj['prerequisites']}")
                    all_courses.append(course_obj)



    with open("data\scraped\prereqs.json", "w") as f:
        json.dump(all_courses, f, indent=2)

        #             # insert into `prereqs` for prerequisites
        #             course_id = get_course_id(course["courseNumber"], curr)
        #             for prereq in course_obj["prerequisites"]:
        #                 prereq_id = get_course_id(prereq, curr)
        #                 if prereq_id and course_id:
        #                     curr.execute("""
        #                     INSERT INTO prereqs (course_id, prereq_id)
        #                     VALUES (%s, %s)
        #                     ON CONFLICT (course_id, prereq_id) DO NOTHING
        #                     """, (course_id, prereq_id))
        #                 else:
        #                     print(f"❌Prerequisite {prereq} not found for course {course_obj['courseNumber']}")

        #             conn.commit()
        #             time.sleep(0.1)
        #             # print(f"✅successfully processed {course_obj['courseNumber']}!\n")
        # num_courses = len(data)
        # print(f"🎯🎯🎯Finished processing {num_courses} courses!")

if __name__ == "__main__":
    main()

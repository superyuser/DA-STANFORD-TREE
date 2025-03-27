from ollama import chat
from tqdm import tqdm
from initialize_database import create_tables, DB_PARAMS
import psycopg2
import json
import re
import os
import time


PROMPT_TEMPLATE = """
You are a course advisor for Stanford University. You will be given a course description. Your task is to extract the courses listed as **prerequisites** and return them as a **JSON list**, like this:

["CS 106A", "CS 107", "Linear Algebra"]

Only return the JSON list and nothing else — no explanations, no formatting, no labels. Add all course numbers found in the description to the list. If not, return an empty list: `[]`.

Follow these rules in order of priority:

1. **If specific course numbers are listed as prerequisites**, extract all of them in the format "SUBJECT CODE" (e.g., "CS 106A"). 
   - Add a space between the subject and number (e.g., "CS106A" → "CS 106A").
   - Include all course codes explicitly listed in the text, even if they’re in parentheses or embedded in sentences.
   - Always include the full course code with both subject and number, even if only the number is mentioned in the text. 
   - The current course is from the {subject} department. Use this subject for any course numbers that are missing one.

2. **If there are no course numbers**, extract **clear verbal prerequisite descriptions** (e.g., "Linear Algebra", "Introductory Biology").
   - Exclude vague or general phrases like "mathematical maturity", "strong programming skills", or "background in statistics".
   - Always exclude "consent of instructor" and any similar phrases.

3. If **no prerequisites are mentioned**, return an empty list: `[]`.

Now, analyze the following course description and return the JSON list only:

{courseDescription}
"""

ORIGINAL_JSON_FILE = r"data\scraped\courses_per_department_all.json"
JSON_FILE = r"data\scraped\courses_per_department_unique.json"

def get_all_courses():
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
        return [entry["courseNumber"] for entry in data]

def clean_courses(original_file = ORIGINAL_JSON_FILE, output_file = JSON_FILE):
    unique_data = []
    with open(original_file, "r") as f:
        data = json.load(f)
        for course in data:
            if course not in unique_data:
                unique_data.append(course)

        with open(output_file, "w") as w:
            json.dump(unique_data, w, indent=4)

def eda():
    with open(ORIGINAL_JSON_FILE, "r") as f:
        data = json.load(f)
        print(f"✨Number of courses: {len(data)}")
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
        print(f"✨Number of unique courses: {len(data)}")

def generate_prompt(subject, courseDescription):
    return PROMPT_TEMPLATE.format(subject=subject, courseDescription=courseDescription)

def clean_course_codes(result):
    pattern = re.compile(r"[A-Z]{2,}\s?\d{1,4}[A-Z]?")
    cleaned_results = []
    for code in result:
        cleaned_results.extend(re.findall(pattern, code.strip()))
    # print(f"✨Cleaned codes: {cleaned_results}")
    space_pattern = re.compile(r"([A-Z]{2,})\s?(\d{1,4})([A-Z]?)")
    normalized_results = []
    for course in result:
        match = space_pattern.match(course)
        if match:
            course_num, course_title, course_letter = match.groups()
            normalized_results.append(f"{course_num} {course_title}{course_letter}")
    # print(f"✨Normalized codes: {normalized_results}")
    return normalized_results

def process_pres(result, valid_courses):
    just_codes = clean_course_codes(result)
    return [i for i in just_codes if i in set(valid_courses)]

def main():
    
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
        for course in data[1000:1020]:
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
                raw_result = response["message"]["content"]

            time.sleep(0.05)
            course_obj["prerequisites"] = process_pres(raw_result, get_all_courses())
            print(f"{course_obj['courseNumber']} → {course_obj['prerequisites']}\n{course_obj['courseDescription']}\n\n")
        print(f"🌬️🌬️🌬️ Done populating prereqs.")

if __name__ == "__main__":
    to_add = []
    print("jhi!")
    with open(JSON_FILE, "r") as f:
        print("Loading data...")
        lookat = json.load(f)
        for course in tqdm(lookat):
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
                raw_result = response["message"]["content"]

            time.sleep(0.05)
            course_obj["prerequisites"] = process_pres(raw_result, get_all_courses())
            to_add.append(course_obj)
    with open(r"data\processed\this_is_different.json", "w") as f:
        json.dump(to_add, f, indent=4)
    print("Done!!!!!")
            
        

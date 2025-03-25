from ollama import chat
from tqdm import tqdm
import json
import re

# performs baby checks of dataset

all_courses = []
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

valid_courses = get_all_courses()


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

def process_pres(result):
    just_codes = clean_course_codes(result)
    normalize_codes = normalize_course_codes(just_codes)
    valid_codes = [code for code in normalize_codes if code in valid_courses]
    print(f"✨Matching valid codes: {valid_codes}")
    invalid_codes_to_print = [code for code in normalize_codes if code not in valid_courses]
    # print(f"💔Invalid codes: {invalid_codes_to_print}")
    return valid_codes

with open("data\scraped\courses_cs_all.json", "r") as f:
    data = json.load(f)
    for course in data[5000:5030]:
        course_obj = course
        course_obj["prerequisites"] = []
        
        messages = [
            {
                "role": "user",
                "content": generate_prompt(course_obj["courseNumber"].split(" ")[0], course_obj["courseDescription"])
            }
        ]

        response = chat("llama3.2", messages)

        raw_result = json.loads(response["message"]["content"])
        course_obj["prerequisites"] = process_pres(raw_result)
        all_courses.append(course_obj)

# print(f"🍚Saving to json...")

# with open("data\processed\courses_cs_pres.json", "w") as f:
#     json.dump(all_courses, f, indent=4)
# print(f"✨✨Saved to json: {len(all_courses)} courses with prerequisites✨✨")

    
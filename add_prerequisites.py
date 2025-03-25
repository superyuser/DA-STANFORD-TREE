from ollama import chat
import json

# performs baby checks of dataset

all_courses = []

PROMPT_TEMPLATE = """
You are a course advisor for Stanford University. You are given a course description. Please return the prerequisites in the following JSON list format: ["req1", "req2", ...], do not return anything else. Return results according to the following hierarchy:
1. Specific course numbers extracted from the text; note that the course numbers should be returned as an acronym of the course followed by the number (e.g., CS 106A), with a space in between (e.g, CS106A -> CS 106A). Extract all course numbers from the text that are listed as prerequisites.
2. Verbal descriptions of the prerequisites, excluding the course numbers; note that if the verbal description is vague or pertaining to a general topic, exclude it from the list.
3. If none exists, return an empty list. 

Here is the course description:
{courseDescription}
"""

def generate_prompt(courseDescription):
    return PROMPT_TEMPLATE.format(courseDescription=courseDescription)

with open("data\scraped\courses_per_department_all.json", "r") as f:
    data = json.load(f)
    for course in data:
        course_obj = course
        course_obj["prerequisites"] = []
        
        messages = [
            {
                "role": "user",
                "content": generate_prompt(course_obj["courseDescription"])
            }
        ]

        response = chat("llama3.2", messages)

        course_obj["prerequisites"] = response["message"]["content"]
        print(f"🧪 Raw response for {course_obj['courseNumber']}: {course_obj["prerequisites"]}")
        all_courses.append(course_obj)

print(f"✨✨✨Added {len(all_courses)} courses with prerequisites✨✨✨")
    
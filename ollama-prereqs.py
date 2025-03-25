from ollama import chat
import json

PROMPT_TEMPLATE = """
You are a course advisor for Stanford University. You are given a course description. Please return the requisites in the following JSON list format, returning nothing else:
["req1", "req2", ...].

Here is the course description:
{courseDescription}
"""

def generate_prompt(courseDescription):
    return PROMPT_TEMPLATE.format(courseDescription=courseDescription)

# c1 = "Is it bad if you lie to ChatGPT? Who is to blame if ChatGPT lies? Should we let superhuman AI make life and death decisions? These questions ask whether advanced AI systems (today, often large language models - LLMs) can be moral agents - whether they are the kind of thing that can know how to make (ethically) correct decisions, and be held responsible for the rights or wrongs they do. Asking these questions leads us to questions about ourselves: What about us makes us moral agents? Is it our reason? Or is it essential that we emotionally feel each others' pain? Is selfishness irrational, or just unpleasant? Understanding ourselves can help us think about what kinds of artificial minds we would like to make, and, if we can, how. In this class, we provide the philosophical rigor and technical background necessary to robustly interrogate these and related questions. Readings will be drawn from philosophy, deep learning, and the cognitive sciences. The major assessment in this class will be a term project. There will be reading assignments for every class, and a mix of lectures, discussions, and participatory in-class activities. Recommended prerequisites: PHIL 80 or multiple philosophy courses; CS 183."

course_data = {
    "name": "CS 183",
    "description": c1,
    "prerequisites": []
}


messages = [
    {
        "role": "user",
        "content": generate_prompt(c1)
    }
]

response = chat("gemma3", messages)

course_data["prerequisites"] = json.loads(response["message"]["content"])

# must add a section where each of the prereqs are matched to existing courses in database, if dne, add course data (pointers to null); 
# might need to do some cleaning (uniform formatting for course nums)

print(course_data)

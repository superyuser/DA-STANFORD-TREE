import json

with open(f"courses_per_department_all.json", "r") as f:
    data = json.load(f)
    print(len(data))
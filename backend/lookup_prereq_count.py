import json
import os

JSON_FILE = "data\\execute\\all_courses.json"

pairs = []


def main():
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
        for course in data:
            if len(course['prerequisites']) == 0:
                continue
            else:
                for prereq in course['prerequisites']:
                    pairKey = f"{course['courseNumber']}_{prereq}"
                    if pairKey in pairs:
                        continue
                    pairs.append(pairKey)
    print(pairs)

    print(f"{len(set(pairs))} pairs found")

if __name__ == "__main__":
    main()

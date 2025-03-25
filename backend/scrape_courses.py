from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm
import json
import os
import time
import datetime
import re

# user enters DEPARTMENT THEY WANT TO SCRAPE, NUM COURSES (default = 10) -> returns JSON of scraped data

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
OUTPUT_DIR = "./data/scraped"
DEPARTMENT_FILEPATH = "./data/departments.json"

def get_url(code):
    # this is just for spring 24-25, but can be tweaked for other quarters later if necessary
    all_quarters_query_a = "https://explorecourses.stanford.edu/print?q=a&descriptions=on&filter-term-Winter=on&academicYear=&filter-term-Summer=on&filter-term-Autumn=on&filter-term-Spring=on&page=0&filter-coursestatus-Active=on&collapse=&catalog="
    return all_quarters_query_a

def scrapekCourses(code, k="all"):
    results = []
    allClassContainers = driver.find_elements(By.CLASS_NAME, "searchResult")
    addedCount = 0
    if k == "all":
        k = len(allClassContainers)
    for container in allClassContainers[:k]:
        courseNumber = container.find_element(By.CLASS_NAME, "courseNumber").text[:-1]
        courseName = container.find_element(By.CLASS_NAME, "courseTitle").text
        courseDescription = container.find_element(By.CLASS_NAME, "courseDescription").text
        results.append({
            "courseNumber": courseNumber,
            "courseName": courseName,
            "courseDescription": courseDescription
        })
        addedCount += 1
        # print(f"{courseName} ({courseNumber})")
    return results

def writeToJSON(data, filename):
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
    with open(f'{OUTPUT_DIR}/{filename}.json', 'a') as f:
        json.dump(data, f, indent=4)
    # print(f"Wrote {len(data)} courses to {filename}!")

def getAllCoursesFor(code, k="all"):
    driver.get(url=get_url(code))
    data = scrapekCourses(code, k)
    return data

def retrieveDepartmentCode():
    with open(DEPARTMENT_FILEPATH, "r") as f:
        return [line["code"] for line in json.load(f)]

def getAllCoursesForAllDeps(k=10):
    filename = f"courses_per_department_{k}"
    departments = retrieveDepartmentCode()
    allCourses = []
    for department in tqdm(departments, desc="Scraping departments", unit="department"):
        print(f"[STARTING]: {department}")
        allCourses.extend(getAllCoursesFor(department, k=k))
    print("[COMPLETED]: All departments scraped!")
    writeToJSON(allCourses, filename)

if __name__ == "__main__":
    k = input("Enter number of courses to scrape (default = 10): ")
    getAllCoursesForAllDeps(k)
    driver.close()

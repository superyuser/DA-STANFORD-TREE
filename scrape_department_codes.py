import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm
import datetime
import re

START_URL = "https://explorecourses.stanford.edu/"
OUTPUT_DIR = "./data"
    
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get(url=START_URL)

def firstScan():
    departmentsContainer = driver.find_element(By.CLASS_NAME, "departmentsContainer")
    departmentsItems = departmentsContainer.find_elements(By.TAG_NAME, "a")
    print(f"found {len(departmentsItems)} items!")
    departments = []

    for dep in departmentsItems:
        name = dep.text
        departments.append(name)

    return departments

def cleanNames(names):
    foundNames = []
    pattern = r'^(.+)\s\(([A-Z&]+)\)$'
    for name in names:
        match = re.match(pattern, name)
        if match:
            cleanedNames = {
                'name': '',
                'code': ''
            }
            cleanedNames['name'] = match.group(1)
            cleanedNames['code'] = match.group(2)
            foundNames.append(cleanedNames)
    return foundNames

def writeToJSON(departmentDict: dict):
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
    with open(f'{OUTPUT_DIR}/departments.json', 'w') as f:
        json.dump(departmentDict, f, indent=4)
    print(f"Wrote {len(departmentDict)} departments to {OUTPUT_DIR}/departments.json!")

def cleanUp():
    driver.close()

def run():
    print("[SCANNING DEPARTMENTS]")
    departments = firstScan()
    print(f"[COMPLETED SCAN]: {len(departments)} departments found!")
    cleanedNames = cleanNames(departments)
    print(f"[COMPLETED CLEANING]: {len(cleanedNames)} departments cleaned!")
    writeToJSON(cleanedNames)
    print("[COMPLETED WRITE TO JSON]")
    cleanUp()
    print("[CLOSED DRIVER]")

if __name__ == "__main__":
    run()
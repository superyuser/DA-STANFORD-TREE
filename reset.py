import os

OUTPUT_DIR = "./data/scraped"

def resetTargetDir():
    for file in os.listdir(OUTPUT_DIR):
        os.remove(f"{OUTPUT_DIR}/{file}")

resetTargetDir()
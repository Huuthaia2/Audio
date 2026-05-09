import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOMTAT_DIR = os.path.join(BASE_DIR, "Tóm tắt")

def get_categories():
    categories = {}
    if not os.path.isdir(TOMTAT_DIR): 
        print(f"Error: {TOMTAT_DIR} is not a directory")
        return categories
    for d in os.listdir(TOMTAT_DIR):
        if os.path.isdir(os.path.join(TOMTAT_DIR, d)):
            display_name = re.sub(r'^\d+-', '', d)
            categories[d] = display_name
    return categories

print(get_categories())

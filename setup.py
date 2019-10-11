#!/usr/bin/env python3
import pip
import os
import sys


def install(package):
    if hasattr(pip, 'main'):
        pip.main(['install', package])

def install_requirements():
    with open('requirements.txt', 'r') as f:
        for module in f.readline():
            install(module)

def add_symlink():
    mod_path = os.path.dirname(os.path.abspath(__file__)) 
    os.symlink(f"{mod_path}/igfollowers.py", '/usr/local/bin/igfollowers')


if __name__ == "__main__":
    try:
        install_requirements()
    except:
        print("Couldnt install all necessary requirements. Try manually installing with `pip install -r requirements.txt`")
    if len(sys.argv) > 1 and sys.argv[1] == '--link':
        try:
            add_symlink()
        except:
            print("Unable to add symlink.")

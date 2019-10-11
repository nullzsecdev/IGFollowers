#!/usr/bin/env python3
import pip
import os


def install(package):
    if hasattr(pip, 'main'):
        pip.main(['install', package])
    else:
        pip._internal.main(['install', package])

def install_requirements():
    with open('requirements.txt', 'r') as f:
        for module in f.readline():
            install(module)

def add_symlink():
    mod_path = os.path.dirname(os.path.abspath(__file__)) 
    os.symlink(f"{mod_path}/igfollowers.py", '/usr/local/bin/igfollowers')


if __name__ == "__main__":
    install_requirements()
    add_symlink()


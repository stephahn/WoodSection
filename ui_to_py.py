__author__ = 'Stephan'
import os

for file in os.listdir('.'):
    if file.endswith(".ui"):
        os.system("pyside-uic "+file+" -o "+os.path.splitext(file)[0]+".py")
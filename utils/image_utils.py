import os
import shutil

TEMP_DIR = "temp_images"

def cleanup_temp_directory():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

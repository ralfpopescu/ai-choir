from util import get_models
import os

models = get_models()

files = ['./output/to_convolve.mp3','./so-vits-svc/so-vits-svc-4.1-Stable/raw/input.wav']

for folder, spk in models:
    files.append(f"./output/{spk}.mp3")

for file_name in files:
    try:
        os.remove(file_name)
        print(f"Cleaned up: {file_name}")
    except FileNotFoundError:
        print(f"File not found: {file_name}")
    except PermissionError:
        print(f"Permission denied: {file_name}")
    except Exception as e:
        print(f"Error deleting {file_name}: {e}")
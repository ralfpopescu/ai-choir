import subprocess
import os
import json
import shutil
import sys
from util import get_models

def build_command(speaker, folder):
    return [
    'python3', 'inference_main.py',
    '-c', f'../../models/{folder}/config.json',
    '-m', f'../../models/{folder}/model.pth',
    '-n', 'input.wav',
    '-s', speaker
]

def move_and_rename_file(file_path, destination_dir):
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    
    destination_path = os.path.join(destination_dir, 'input.wav')
    shutil.copy(file_path, destination_path)
    print(f"File copied and renamed to: {destination_path}")

# Example usage
# copy_and_rename_file('path/to/original/file.wav', 'path/to/destination/dir')


def is_wav_file(file_path):
    return file_path.lower().endswith('.wav')

# Create a copy of the current environment
my_env = os.environ.copy()

# Update the PATH variable to include additional paths
my_env["PATH"] = f"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:{my_env['PATH']}"

if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_wav_file>")
        sys.exit(1)
    
file_path = sys.argv[1]

if not os.path.isfile(file_path):
    print(f"Error: The file '{file_path}' does not exist.")
    sys.exit(1)

if not is_wav_file(file_path):
    print(f"Error: The file '{file_path}' is not a WAV file.")
    sys.exit(1)
    
destination_dir = './so-vits-svc/so-vits-svc-4.1-Stable/raw'
move_and_rename_file(file_path, destination_dir)

models = get_models()

original_directory = os.getcwd()
os.chdir('./so-vits-svc/so-vits-svc-4.1-Stable')

# generate output for each model
for folder, spk in models:
    command = build_command(spk, folder)
    process = subprocess.Popen(command, env=my_env)
    process.wait()

os.chdir(original_directory)
# process each individual voice
command = ['python3', 'gen_process.py']
process = subprocess.Popen(command, env=my_env)
process.wait()

# combine them all into the choir
command = ['python3', 'gen_combine.py']
process = subprocess.Popen(command, env=my_env)
process.wait()

print('Done! See result in output folder.')
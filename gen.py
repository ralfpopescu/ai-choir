import subprocess
import os
import json
import shutil
import sys
from util import get_models, run_command, check_config

check_config()

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


run_command(['python3', 'setup_env.py'])
    
destination_dir = './so-vits-svc/so-vits-svc-4.1-Stable/raw'
move_and_rename_file(file_path, destination_dir)

models = get_models()

original_directory = os.getcwd()
os.chdir('./so-vits-svc/so-vits-svc-4.1-Stable')

generate output for each model
for folder, spk in models:
    run_command(build_command(spk, folder))

os.chdir(original_directory)
# process each individual voice
run_command(['python3', 'gen_process.py'])

# curve noisy models
run_command(['python3', 'gen_curve.py'])

# combine them all into the choir
run_command(['python3', 'gen_combine.py'])

# add convolution reverb
run_command(['python3', 'gen_convolve.py'])

# cleanup
run_command(['python3', 'cleanup.py'])

print('Done! See result in output folder.')
import subprocess
import os
import requests
from util import run_command

# Create a copy of the current environment
env = os.environ.copy()

# Update the PATH variable to include additional paths
env["PATH"] = f"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:{env['PATH']}"

# Define the environment name
env_name = "env3.8"

# Check if the environment already exists
if not os.path.exists(env_name):
    print(f"Setting up env for python 3.8...")
    # Create the virtual environment
    run_command(['python3.8', '-m', 'venv', env_name])
else:
    print(f"The virtual environment '{env_name}' already exists.")


# Activate the environment and install requirements
process = subprocess.Popen(f"source {env_name}/bin/activate", env=env, shell=True, executable='/bin/bash')
process.wait()

process = subprocess.Popen("pip3 install -r requirements.txt", env=env, shell=True, executable='/bin/bash')
process.wait()

file_path = 'so-vits-svc/so-vits-svc-4.1-Stable/pretrain/checkpoint_best_legacy_500.pt'

if not os.path.exists('output'):
    os.makedirs('output', exist_ok=True)
    
if not os.path.exists('so-vits-svc/so-vits-svc-4.1-Stable/results'):
    os.makedirs('so-vits-svc/so-vits-svc-4.1-Stable/results', exist_ok=True)

# download content vec
if not os.path.exists(file_path):
    os.makedirs('so-vits-svc/so-vits-svc-4.1-Stable/pretrain', exist_ok=True)

    run_command([
        'curl', 
        '-L', 
        '-o', 'so-vits-svc/so-vits-svc-4.1-Stable/pretrain/checkpoint_best_legacy_500.pt', 
        'https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt'
    ])

# download models
run_command(['python3', 'download_models.py'])


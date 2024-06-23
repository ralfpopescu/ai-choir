import os
import json
import subprocess
import sys

def get_models():
    result = []
    base_path = "./models"
    # Iterate over each folder in the base directory
    for folder_name in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder_name)
        if os.path.isdir(folder_path):
            config_path = os.path.join(folder_path, 'config.json')
            if os.path.isfile(config_path):
                # Read the config.json file
                with open(config_path, 'r') as config_file:
                    config_data = json.load(config_file)
                    # Extract the key under the "spk" field
                    spk_key = list(config_data['spk'].keys())[0]
                    result.append((folder_name, spk_key))
    return result


def get_speakers():
    result = []
    base_path = "./models"
    # Iterate over each folder in the base directory
    for folder_name in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder_name)
        if os.path.isdir(folder_path):
            config_path = os.path.join(folder_path, 'config.json')
            if os.path.isfile(config_path):
                # Read the config.json file
                with open(config_path, 'r') as config_file:
                    config_data = json.load(config_file)
                    # Extract the key under the "spk" field
                    spk_key = list(config_data['spk'].keys())[0]
                    result.append(spk_key)
    return result

def get_config():
    with open('config.json', 'r') as file:
        data = json.load(file)
        print(data)
    return data

def check_config():
    file_path = 'config.json'
    required_fields = [
        "cleanup",
        "convolution_reverb_dry_wet",
        "stereo_spread",
        "drift",
        "base_detune",
        "detune_drift",
        "detune_frequency",
        "output_gain"
    ]
    
    try:
        config = get_config()
    except FileNotFoundError:
        raise Exception(f"The file {file_path} does not exist.")
    except json.JSONDecodeError:
        raise Exception(f"The file {file_path} is not a valid JSON file.")

    missing_fields = [field for field in required_fields if field not in config]

    if missing_fields:
        raise Exception(f"The following required fields are missing in the config: {', '.join(missing_fields)}")

    if config["detune_drift"] * 4 > config["base_detune"]:
        raise Exception(f"detune_drift can't be more than 25% of base_detune")
    
    return config


def run_command(command):
    # Create a copy of the current environment
    env = os.environ.copy()

    # Update the PATH variable to include additional paths
    env["PATH"] = f"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:{env['PATH']}"
    process = subprocess.Popen(command, env=env)
    process.wait()
    if process.returncode != 0:
        print(f"Command {command} failed with return code {process.returncode}")
        sys.exit(process.returncode)
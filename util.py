import os
import json

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
    return data
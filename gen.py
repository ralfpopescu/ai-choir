import subprocess
import os

def build_command(speaker, folder):
    return [
    'python3', '../so-vits/svc/inference_main.py',
    '-c', f'models/{folder}/config.json',
    '-m', f'models/{folder}/model.pth',
    '-n', 'input.wav',
    '-s', speaker
]


# Create a copy of the current environment
my_env = os.environ.copy()

# Update the PATH variable to include additional paths
my_env["PATH"] = f"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:{my_env['PATH']}"

def get_models(base_path):
    result = []
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

models = get_models("./models")

# generate output for each model
for folder, spk in models:
    command = build_command(spk, folder)
    process = subprocess.Popen(command, env=my_env)
    process.wait()

# process each individual voice
command = ['python3', 'gen_process.py']
process = subprocess.Popen(command, env=my_env)
process.wait()

# combine them all into the choir
command = ['python3', 'gen_combine.py']
process = subprocess.Popen(command, env=my_env)
process.wait()
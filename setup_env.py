import subprocess
import os

# Create a copy of the current environment
my_env = os.environ.copy()

# Update the PATH variable to include additional paths
my_env["PATH"] = f"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:{my_env['PATH']}"

# Define the environment name
env_name = "env3.8"

# Check if the environment already exists
if not os.path.exists(env_name):
    # Create the virtual environment
    command = ['python3.8', '-m', 'venv', env_name]
    process = subprocess.Popen(command, env=my_env)
    process.wait()
else:
    print(f"The virtual environment '{env_name}' already exists.")


# Activate the environment and install requirements
activate_and_install = f"source {env_name}/bin/activate && pip3 install -r requirements.txt"
process = subprocess.Popen(activate_and_install, env=my_env, shell=True, executable='/bin/bash')
process.wait()
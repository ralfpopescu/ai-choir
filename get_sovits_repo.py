import subprocess
import zipfile
import os

def unzip_file(zip_file_path, extract_to_path):
    # Ensure the directory to extract to exists
    if not os.path.exists(extract_to_path):
        os.makedirs(extract_to_path)
    
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to_path)

# Create a copy of the current environment
my_env = os.environ.copy()

# Update the PATH variable to include additional paths
my_env["PATH"] = f"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:{my_env['PATH']}"

# download so-vits-svc
if not os.path.exists('so-vits-svc.zip') and not os.path.exists('so-vits-svc'):
    command = ['curl', '-L', '-o', 'so-vits-svc.zip', 'https://github.com/svc-develop-team/so-vits-svc/archive/refs/heads/4.1-Stable.zip']
    process = subprocess.Popen(command, env=my_env)
    process.wait()

if not os.path.exists('so-vits-svc'):
    zip_file_path = 'so-vits-svc.zip'
    extract_to_path = 'so-vits-svc'
    unzip_file(zip_file_path, extract_to_path)
 
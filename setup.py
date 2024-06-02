import subprocess
import os

def check_command(command):
    try:
        subprocess.check_output(['which', command])
        print(f"{command} is installed.")
    except subprocess.CalledProcessError:
        print(f"{command} is not installed. You should install {command}.")
        sys.exit(1)

# Check for git and python3
check_command('git')
check_command('python3')

# Create a copy of the current environment
my_env = os.environ.copy()

# Update the PATH variable to include additional paths
my_env["PATH"] = f"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:{my_env['PATH']}"

# clone so-vits-svc
command = ['git', 'clone', 'https://github.com/svc-develop-team/so-vits-svc.git']
process = subprocess.Popen(command, env=my_env)
process.wait()

# download content vec
command = ['wget', '-P', 'so-vits-svc/pretrain/', 'https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt', '-0', 'checkpoint_best_legacy_500.pt']
process = subprocess.Popen(command, env=my_env)
process.wait()

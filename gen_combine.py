from pydub import AudioSegment
from pydub.effects import normalize, pan
from util import get_models

pan_amount = 0.2

models = get_models()

files = []
for folder, spk in models:
    files.append(f"./output/{spk}.mp3")

# Load and normalize each file
normalized_audios = []
for file in files:
    audio = AudioSegment.from_file(file, format="mp3")
    normalized_audio = normalize(audio)
    normalized_audios.append(normalized_audio)

# Pan each normalized audio file slightly left or right, alternating
panned_audios = []
for i, audio in enumerate(normalized_audios):
    panned_audio = pan(audio, pan_amount if i % 2 == 0 else (pan_amount * -1.0))  # Adjust pan value as needed
    panned_audios.append(panned_audio)

# Overlay all the panned audio files
overlayed = panned_audios[0]
for audio in panned_audios[1:]:
    overlayed = overlayed.overlay(audio)

# Export the combined audio file as MP3
overlayed.export(f"./output/generation_at_{str(int(time.time()))}.mp3", format="mp3")

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
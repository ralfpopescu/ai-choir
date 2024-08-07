from pydub import AudioSegment
from pydub.effects import normalize, pan
from util import get_models, get_config
import time
import random
import os

config = get_config()
pan_amount = config["stereo_spread"]

models = get_models()

files = []
for folder, spk in models:
    files.append(f"./output/{spk}.mp3")

file_to_pan = {
    "./output/female-1.mp3": 0,
    "./output/female-2.mp3": 0.25,
    "./output/female-3.mp3": 0.2,
    "./output/female-4.mp3": -0.25,
    "./output/male-1.mp3": 0.15,
    "./output/male-2.mp3": -0.2,
    "./output/male-3.mp3": -0.15,
}

file_to_gain_key = {
    "./output/female-1.mp3": "voice_gain_female_1",
    "./output/female-2.mp3": "voice_gain_female_2",
    "./output/female-3.mp3": "voice_gain_female_3",
    "./output/female-4.mp3": "voice_gain_female_4",
    "./output/male-1.mp3": "voice_gain_male_1",
    "./output/male-2.mp3": "voice_gain_male_2",
    "./output/male-3.mp3": "voice_gain_male_3",
}

def get_random_pan():
    return random.randrange(0, 25) / 100

# Load and normalize each file
normalized_audios = []
for file in files:
    audio = AudioSegment.from_file(file, format="mp3")

     # Apply gain
    gain_key = file_to_gain_key.get(file, None)
    if gain_key and gain_key in config:
        gain_value = config[gain_key]
        audio = audio + gain_value

    normalized_audio = normalize(audio)
    normalized_audios.append(normalized_audio)

# Pan each normalized audio file slightly left or right, alternating
panned_audios = []
for i, audio in enumerate(normalized_audios):
    # produce a random pan if we've added unaccounted models
    file_pan = 0
    if files[i] in file_to_pan:
        file_pan = file_to_pan[files[i]]
    else:
        file_pan = get_random_pan()
    panned_audio = pan(audio, pan_amount * file_pan)  # Adjust pan value as needed
    panned_audios.append(panned_audio)

# Overlay all the panned audio files
overlayed = panned_audios[0]
for audio in panned_audios[1:]:
    overlayed = overlayed.overlay(audio)

# Export the combined audio file as MP3
overlayed.export("./output/to_convolve.mp3", format="mp3")

from pydub import AudioSegment
import math
import os
from util import get_speakers, get_config
import random

config = get_config()

def gen_input_file(speaker):
    return f'./so-vits-svc/so-vits-svc-4.1-Stable/results/input.wav_0key_{speaker}_sovits_pm.flac'

base_detune = config["base_detune"]

def generate_amount(idx):
    if idx % 6 == 0:
        return base_detune / 2
    if idx % 2 == 0:
        return base_detune + (idx % 4 * config["detune_drift"])
    return base_detune - (idx % 4 * config["detune_drift"])

def generate_random_segment_length():
    return random.randrange(400,1100)

segment_lengths = [400, 600, 800, 1000, 500, 700, 900]

# Function to change speed
def change_speed(segment, speed=1.0):
    return segment._spawn(segment.raw_data, overrides={
        "frame_rate": int(segment.frame_rate * speed)
    }).set_frame_rate(segment.frame_rate)

# Process each input file
for idx, speaker in enumerate(get_speakers()):
    file = gen_input_file(speaker)
    amount = generate_amount(idx)

    # just in case a new model is added to the folder, we'll check for that
    segment_length = 100
    if(idx >= len(segment_lengths)):
        segment_length = generate_random_segment_length()
    else:
        segment_length = segment_lengths[idx]

    segment_length = int(segment_length * config["detune_frequency"])

    # Load the audio file
    audio = AudioSegment.from_file(file)

    # Duration of the audio in milliseconds
    duration_ms = len(audio)

    # Lists to hold the processed segments
    processed_segments = []

    # Determine if the file should start by slowing down or speeding up
    start_slow_down = idx % 2

    # Process each segment
    for i in range(0, duration_ms, segment_length):
        segment = audio[i:i + segment_length]
        if start_slow_down:
            # Slow down: speed < 1
            speed = 1.0 - amount
        else:
            # Speed up: speed > 1
            speed = 1.0 / (1.0 - amount)

        # Change the speed of the segment
        processed_segment = change_speed(segment, speed)

        # Adjust the length of the processed segment to match the original segment length
        if speed < 1:
            processed_segment = processed_segment + AudioSegment.silent(duration=(segment_length - len(processed_segment)))
        else:
            processed_segment = processed_segment[:segment_length]

        # Append the processed segment to the list
        processed_segments.append(processed_segment)

        # Toggle the start_slow_down flag for the next segment
        start_slow_down = not start_slow_down

    # Combine all processed segments
    final_audio = sum(processed_segments)

    final_audio = final_audio + config["output_gain"]

    # Export the final audio
    final_audio.export(f"./output/{speaker}.mp3", format="mp3")
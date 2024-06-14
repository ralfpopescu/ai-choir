from pydub import AudioSegment
import math
import os
from util import get_speakers
import random

def gen_input_file(speaker):
    return f'./so-vits-svc/so-vits-svc-4.1-Stable/results/input.wav_0key_{speaker}_sovits_pm.flac'

base_detune = .014

def generate_amount(idx):
    if idx % 2 == 0:
        return base_detune + (idx % 4 * 0.001)
    return base_detune - (idx % 4 * 0.001)

def generate_segment_length():
    return int(random.uniform(400, 1000))


# Function to change speed
def change_speed(segment, speed=1.0):
    return segment._spawn(segment.raw_data, overrides={
        "frame_rate": int(segment.frame_rate * speed)
    }).set_frame_rate(segment.frame_rate)

# Process each input file
for idx, speaker in enumerate(get_speakers()):
    file = gen_input_file(speaker)
    amount = generate_amount(idx)
    segment_length = generate_segment_length()

    # Load the audio file
    audio = AudioSegment.from_file(file)

    # Duration of the audio in milliseconds
    duration_ms = len(audio)

    # Lists to hold the processed segments
    processed_segments = []

    # Determine if the file should start by slowing down or speeding up
    if idx % 2 == 0:
        start_slow_down = True
    else:
        start_slow_down = False

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

    final_audio = final_audio - 10

    # Export the final audio
    final_audio.export(f"./output/{speaker}.mp3", format="mp3")
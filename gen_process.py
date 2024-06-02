from pydub import AudioSegment
import math

def gen_input_file(speaker):
    return f'./so-vits-svc/results/input.wav_0key_{speaker}_sovits_pm.flac'

def generate_amount():
    return random.uniform(0.012, 0.18)

def generate_segment_length():
    return random.uniform(450, 950)

def get_speakers(base_path):
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
                    result.append(spk_key)
    return result

# Dictionary to store input file names, amount, and segment_length for each file
input_files = {
    "input1": {"file": gen_input_file('billie'), "amount": 0.017, "segment_length": 600},
    "input2": {"file": gen_input_file('troy'), "amount": 0.018, "segment_length": 700},
    "input3": {"file": gen_input_file('katy'), "amount": 0.015, "segment_length": 450},
    "input4": {"file": gen_input_file('sza'), "amount": 0.018, "segment_length": 900},
    "input5": {"file": gen_input_file('hoppus'), "amount": 0.013, "segment_length": 880},
    "input6": {"file": gen_input_file('elton'), "amount": 0.016, "segment_length": 550}
}

# Accessing a sample value
print(input_files["input1"]["file"])


# Function to change speed
def change_speed(segment, speed=1.0):
    return segment._spawn(segment.raw_data, overrides={
        "frame_rate": int(segment.frame_rate * speed)
    }).set_frame_rate(segment.frame_rate)

# Process each input file
for idx, speaker in enumerate(get_speakers("./models")):
    file = gen_input_file(speaker)
    amount = generate_amount()
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

    # Export the final audio
    final_audio.export(f"./output/{speaker}.mp3", format="mp3")
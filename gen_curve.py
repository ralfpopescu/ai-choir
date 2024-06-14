import librosa
import numpy as np
import soundfile as sf

should_curve_filenames = ['female-3.mp3', 'male-2.mp3', 'male-4.mp3']

# Iterate over input files 1-6
for filename in should_curve_filenames:
    # Load the two audio files
    input_file1, sr1 = librosa.load(f"./output/{filename}")
    input_file2, sr2 = librosa.load("./so-vits-svc/so-vits-svc-4.1-Stable/raw/input.wav")

    # Calculate the envelope of the second file using a simple moving average filter
    frame_length = 512
    hop_length = 256
    envelope2 = np.abs(librosa.util.frame(input_file2, frame_length=frame_length, hop_length=hop_length)).mean(axis=0)

    # Apply the envelope to the first file
    envelope1 = np.interp(
        np.linspace(0, 1, len(input_file1)),
        np.linspace(0, 1, len(envelope2)),
        envelope2
    )
    output_file1 = input_file1 * envelope1
    output_file1 *= 5

    # Save the output file
    sf.write(f"./output/{filename}", output_file1, sr1)

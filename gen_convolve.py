import librosa
import soundfile as sf
from scipy.signal import convolve
import numpy as np

# Load the input audio file (vocal) in stereo
input_signal, input_samplerate = librosa.load('./output/to_convolve.mp3', sr=None, mono=False)

# Load the convolution signal (clap in a room) in stereo
convolution_signal, convolution_samplerate = librosa.load('impulse.wav', sr=None, mono=False)

# Ensure both signals have the same sample rate
if input_samplerate != convolution_samplerate:
    raise ValueError("Sample rates of input and convolution signals do not match")

# Check if the signals are stereo and handle each channel separately
if input_signal.ndim == 1:
    # Both signals are mono
    convolved_signal = convolve(input_signal, convolution_signal, mode='full')

    # Normalize the convolved signal to prevent clipping
    convolved_signal = convolved_signal / np.max(np.abs(convolved_signal))

    # Trim or pad the convolved signal to match the length of the input signal
    if len(convolved_signal) > len(input_signal):
        convolved_signal = convolved_signal[:len(input_signal)]
    else:
        convolved_signal = np.pad(convolved_signal, (0, len(input_signal) - len(convolved_signal)), 'constant')

    # Mix the dry and wet signals (50% dry, 50% wet)
    dry_wet_ratio = 0.6
    mixed_signal = dry_wet_ratio * convolved_signal + (1 - dry_wet_ratio) * input_signal

else:
    # Both signals are stereo
    convolved_signal = []
    for channel in range(input_signal.shape[0]):
        # Perform convolution on each channel separately
        convolved_channel = convolve(input_signal[channel], convolution_signal[channel], mode='full')

        # Normalize the convolved signal to prevent clipping
        convolved_channel = convolved_channel / np.max(np.abs(convolved_channel))

        # Trim or pad the convolved signal to match the length of the input signal
        if len(convolved_channel) > len(input_signal[channel]):
            convolved_channel = convolved_channel[:len(input_signal[channel])]
        else:
            convolved_channel = np.pad(convolved_channel, (0, len(input_signal[channel]) - len(convolved_channel)), 'constant')

        convolved_signal.append(convolved_channel)

    # Convert the list of channels back to a NumPy array
    convolved_signal = np.array(convolved_signal)

    dry_wet_ratio = 0.5
    # Mix the dry and wet signals (50% dry, 50% wet) for each channel
    mixed_signal = []
    for channel in range(input_signal.shape[0]):
        mixed_channel = dry_wet_ratio * convolved_signal[channel] + (1 - dry_wet_ratio) * input_signal[channel]
        mixed_signal.append(mixed_channel)

    # Convert the list of channels back to a NumPy array
    mixed_signal = np.array(mixed_signal)

# Normalize the mixed signal to prevent clipping
max_val = np.max(np.abs(mixed_signal))
mixed_signal = mixed_signal / max_val

# Save the mixed signal to a new audio file
sf.write(f"./output/generation_at_{str(int(time.time()))}.mp3", mixed_signal.T, input_samplerate)

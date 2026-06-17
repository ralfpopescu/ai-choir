from pydub import AudioSegment
from pydub.effects import normalize, pan
from util import get_models, get_config


file_to_pan_key = {
    "./output/female-1.wav": "voice_pan_female_1",
    "./output/female-2.wav": "voice_pan_female_2",
    "./output/female-3.wav": "voice_pan_female_3",
    "./output/female-4.wav": "voice_pan_female_4",
    "./output/male-1.wav": "voice_pan_male_1",
    "./output/male-2.wav": "voice_pan_male_2",
    "./output/male-3.wav": "voice_pan_male_3",
}

file_to_gain_key = {
    "./output/female-1.wav": "voice_gain_female_1",
    "./output/female-2.wav": "voice_gain_female_2",
    "./output/female-3.wav": "voice_gain_female_3",
    "./output/female-4.wav": "voice_gain_female_4",
    "./output/male-1.wav": "voice_gain_male_1",
    "./output/male-2.wav": "voice_gain_male_2",
    "./output/male-3.wav": "voice_gain_male_3",
}


def main():
    config = get_config()

    models = get_models()

    files = []
    for folder, spk in models:
        files.append(f"./output/{spk}.wav")

    # Load each file, normalize to a common reference, then apply per-voice gain.
    # Order matters: normalize() rescales the peak back to ~0 dBFS, so it must run
    # BEFORE the gain is applied — otherwise it would undo the user's gain setting.
    normalized_audios = []
    for file in files:
        audio = AudioSegment.from_file(file, format="wav")

        normalized_audio = normalize(audio)

        # Apply per-voice gain (dB) on top of the normalized level
        gain_key = file_to_gain_key.get(file, None)
        if gain_key and gain_key in config:
            gain_value = config[gain_key]
            normalized_audio = normalized_audio + gain_value

        normalized_audios.append(normalized_audio)

    # Pan each voice to its own stereo position (-1 = hard left, +1 = hard right)
    panned_audios = []
    for i, audio in enumerate(normalized_audios):
        pan_key = file_to_pan_key.get(files[i])
        file_pan = config.get(pan_key, 0.0) if pan_key else 0.0
        file_pan = max(-1.0, min(1.0, file_pan))
        panned_audio = pan(audio, file_pan)
        panned_audios.append(panned_audio)

    # Overlay all the panned audio files
    overlayed = panned_audios[0]
    for audio in panned_audios[1:]:
        overlayed = overlayed.overlay(audio)

    # Export the combined audio file as MP3
    overlayed.export("./output/to_convolve.wav", format="wav")


if __name__ == "__main__":
    main()

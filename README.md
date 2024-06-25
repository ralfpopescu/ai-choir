# ai-choir

## Description

ai-choir transforms any singing vocal into a choir rendition, best used to add crowd-like doubles or generally as a supercharged chorus effect. It works by using AI to transform the vocal into several different voices (sopranos, tenors and altos), applying detuning/dequantizing, and layering them together.

demo: https://www.tiktok.com/@popeskasounds/video/7375255624751353131

## Installation

All you need is python3 https://www.python.org/downloads/
Otherwise, all the setup will be handled for you by the script. The first time you run the script will take significantly longer as it installs all the dependencies, and will take up about 4 GB of space (the voice models are about half a gig each!)

## Usage

Transform any wav file like this: `python3 gen.py ./path/to/file.wav`

Additionally, there's a `config.json` where you can play around with some parameters:

"cleanup" (true/false) - whether the script should cleanup iterim files 

"convolution_reverb_dry_wet" (0 - 1.0) - adds convolution reverb to the output. switch out the `impulse.wav` file for whatever impulse response you want!

"stereo_spread" (0 to 4.0) - how panned the voices should be. 0 is mono, 4.0 will be hard left/right.

"base_detune" (0 t0 0.05) - how detuned the voices should be

"detune_drift" (0 to 25% of base_detune) - how much the voices should fluctuate around the base detuning

"detune_frequency" (0 to 5.0) - how long voices will linger on a detuned note

"output_gain" (-inf to inf) - apply gain to the output

If you want to modify the voices of the choir, you can stick any so-vits-svc models into the `models` directory, just make sure the .pth file is called `model.pth`. You may want to tinker with the panning for your model in `gen_combine.py`.

## Contributing

Would love to see additional voice models, processing, and configurations improve the end result of this project. Throw up a PR for anything that sounds cool, and I'll check it out!

## License

ai-choir is licensed under the MIT License. You are free to use, modify, and distribute this software as permitted by the license.



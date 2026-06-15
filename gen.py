import os
import json
import shutil
import sys
from util import get_models, check_config


def build_inference_args(speaker, folder):
    """Build the argument list for inference_main as if it were called from command line."""
    models_path = os.path.abspath('models')
    return [
        'inference_main.py',
        '-c', os.path.join(models_path, folder, 'config.json'),
        '-m', os.path.join(models_path, folder, 'model.pth'),
        '-n', 'input.wav',
        '-s', speaker,
        '-wf', 'wav'
    ]


def move_and_rename_file(file_path, destination_dir):
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    destination_path = os.path.join(destination_dir, 'input.wav')
    shutil.copy(file_path, destination_path)
    print(f"File copied and renamed to: {destination_path}")


def is_wav_file(file_path):
    return file_path.lower().endswith('.wav')


def ensure_directories():
    """Ensure required directories exist (replaces setup_env.py for packaged mode)."""
    os.makedirs('output', exist_ok=True)
    os.makedirs('so-vits-svc/so-vits-svc-4.1-Stable/results', exist_ok=True)
    os.makedirs('so-vits-svc/so-vits-svc-4.1-Stable/raw', exist_ok=True)


def run_inference(speaker, folder):
    """Run so-vits-svc inference by importing and calling inference_main directly."""
    so_vits_dir = os.path.abspath('./so-vits-svc/so-vits-svc-4.1-Stable')
    original_dir = os.getcwd()
    original_argv = sys.argv[:]
    original_path = sys.path[:]

    try:
        # Build args before chdir so the models path resolves against the
        # working directory, not the so-vits-svc directory
        inference_args = build_inference_args(speaker, folder)

        # Add so-vits-svc to Python path so its imports work
        if so_vits_dir not in sys.path:
            sys.path.insert(0, so_vits_dir)

        # Change to so-vits-svc directory (inference expects relative paths)
        os.chdir(so_vits_dir)

        # Set sys.argv as if inference_main.py was called from command line
        sys.argv = inference_args

        # Import and run inference_main
        # Use importlib to force reimport each time (model paths change per voice)
        import importlib
        if 'inference_main' in sys.modules:
            # Need to reload to pick up new sys.argv
            mod = importlib.reload(sys.modules['inference_main'])
        else:
            mod = importlib.import_module('inference_main')

        mod.main()

    finally:
        os.chdir(original_dir)
        sys.argv = original_argv
        sys.path = original_path


def run_generation(input_file, status_callback=None):
    """Run the full choir generation pipeline.

    Args:
        input_file: Path to the input WAV file.
        status_callback: Optional callable(stage, message) for progress updates.
    """
    def emit(stage, msg):
        print(msg)
        if status_callback:
            status_callback(stage, msg)

    check_config()

    emit("setup", "=== STARTING CHOIR GENERATION ===")
    emit("setup", "Stage 1: Setting up environment")
    ensure_directories()

    destination_dir = './so-vits-svc/so-vits-svc-4.1-Stable/raw'
    move_and_rename_file(input_file, destination_dir)

    models = get_models()
    emit("models", f"Stage 2: Found {len(models)} voice models to process")

    # Generate output for each model
    for idx, (folder, spk) in enumerate(models):
        emit("inference", f"Stage 2.{idx+1}: Processing voice model {folder} ({idx+1}/{len(models)})")
        run_inference(spk, folder)
        emit("inference", f"Completed voice model {folder} ({idx+1}/{len(models)})")

    # Process each individual voice
    emit("process", "Stage 3: Post-processing individual voices")
    import gen_process
    gen_process.main()

    # Curve noisy models
    emit("curve", "Stage 4: Applying EQ curves to voices")
    import gen_curve
    gen_curve.main()

    # Formant shaping (pyworld) — skipped automatically when neutral
    emit("formant", "Stage 5: Shaping formants")
    import gen_formant
    gen_formant.main()

    # Combine them all into the choir
    emit("combine", "Stage 6: Combining all voices into choir")
    import gen_combine
    gen_combine.main()

    # Add convolution reverb
    emit("convolve", "Stage 7: Adding convolution reverb")
    import gen_convolve
    gen_convolve.main()

    # Cleanup
    import cleanup
    cleanup.main()

    emit("done", "=== GENERATION COMPLETE ===")
    print('Done! See result in output folder.')


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python gen.py <path_to_wav_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.isfile(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        sys.exit(1)

    if not is_wav_file(file_path):
        print(f"Error: The file '{file_path}' is not a WAV file.")
        sys.exit(1)

    run_generation(file_path)

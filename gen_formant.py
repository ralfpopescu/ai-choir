"""Per-voice formant shaping via the WORLD vocoder (pyworld).

Each rendered voice is decomposed into pitch (f0), spectral envelope (the
formants) and aperiodicity, the envelope is warped along the frequency axis to
shift the formants -- leaving pitch untouched -- and then resynthesized.

  - ``formant_shift`` (-1..1) moves every voice's formants together: negative
    = larger/darker "singer", positive = smaller/brighter. 0 is neutral.
  - ``formant_drift`` (0..1) adds a slow, smooth, independent random waver to
    each voice's formants for a more natural, less static ensemble.

When both are zero the stage is skipped entirely, so output is byte-for-byte
unchanged from the no-formant pipeline.
"""
import numpy as np
import soundfile as sf
from scipy.ndimage import gaussian_filter1d
from util import get_speakers, get_config

try:
    import pyworld as pw
except Exception:  # pragma: no cover - pyworld always ships in the bundle
    pw = None

# formant_shift of +/-1 maps to this max frequency-warp ratio (and its inverse)
MAX_RATIO = 1.3
# formant_drift of 1.0 = this much warp wobble around the base ratio
MAX_DRIFT = 0.15
# The shared "variation frequency" (detune_frequency, lower = faster) is turned
# into the random-walk smoothing window: faster -> less smoothing -> quicker
# waver. WORLD's default hop is 5 ms, so 45 frames is ~225 ms.
SMOOTH_PER_FREQ = 150
MIN_SMOOTH_FRAMES = 8
# Each voice wavers at its OWN rate, not just its own shape: per-voice smoothing
# windows are spread evenly in log-space so the slowest voice wobbles this many
# times slower than the fastest. This is what makes it sound like several
# independent singers rather than one warble applied in unison.
DRIFT_RATE_SPREAD = 4.0


def _warp_envelope(sp, warp_curve):
    """Warp each frame's spectral envelope along frequency by warp_curve[i]."""
    nbins = sp.shape[1]
    idx = np.arange(nbins)
    out = np.empty_like(sp)
    for i in range(sp.shape[0]):
        r = warp_curve[i]
        if r == 1.0:
            out[i] = sp[i]
        else:
            # formant shift by factor r: new[k] = sp[k / r]
            out[i] = np.interp(idx / r, idx, sp[i])
    return out


def formant_process(y, sr, shift, drift, smooth_frames):
    y = np.ascontiguousarray(y, dtype=np.float64)
    f0, t = pw.harvest(y, sr)
    sp = pw.cheaptrick(y, f0, t, sr)
    ap = pw.d4c(y, f0, t, sr)

    base = MAX_RATIO ** shift  # 0 -> 1.0, +1 -> MAX_RATIO, -1 -> 1/MAX_RATIO
    n = sp.shape[0]
    if drift > 0:
        # Fresh random walk each call, so every voice wavers independently
        # (no two voices move the same way at the same time).
        walk = gaussian_filter1d(np.random.randn(n), sigma=smooth_frames)
        walk = walk / (np.max(np.abs(walk)) or 1.0)
        warp = base * (1.0 + MAX_DRIFT * drift * walk)
    else:
        warp = np.full(n, base)

    out = pw.synthesize(f0, _warp_envelope(sp, warp), ap, sr)
    return out.astype(np.float32)


def main():
    config = get_config()
    shift = float(config.get("formant_shift", 0.0))
    drift = float(config.get("formant_drift", 0.0))
    if shift == 0.0 and drift == 0.0:
        return  # neutral: leave voices exactly as they were
    if pw is None:
        print("pyworld unavailable; skipping formant stage")
        return

    # Variation frequency is shared with the detune stage (lower = faster).
    freq = float(config.get("detune_frequency", 0.3))
    base_smooth = max(MIN_SMOOTH_FRAMES, freq * SMOOTH_PER_FREQ)

    speakers = get_speakers()
    nvoices = len(speakers)
    for i, speaker in enumerate(speakers):
        # Give each voice its own waver rate by spreading the smoothing window
        # evenly in log-space across DRIFT_RATE_SPREAD (slowest .. fastest).
        # factor < 1 -> less smoothing -> quicker waver; > 1 -> slower.
        if drift > 0 and nvoices > 1:
            frac = i / (nvoices - 1)  # 0..1
            factor = DRIFT_RATE_SPREAD ** (frac - 0.5)  # 1/sqrt .. sqrt
        else:
            factor = 1.0
        smooth_frames = max(MIN_SMOOTH_FRAMES, base_smooth * factor)

        path = f"./output/{speaker}.wav"
        y, sr = sf.read(path)
        if y.ndim > 1:
            y = y.mean(axis=1)
        out = formant_process(y, sr, shift, drift, smooth_frames)
        peak = np.max(np.abs(out))
        if peak > 1.0:
            out = out / peak
        sf.write(path, out, sr)


if __name__ == "__main__":
    main()

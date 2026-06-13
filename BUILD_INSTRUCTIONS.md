# ai_choir — Build Instructions (macOS)

## One-time setup

1. **Python 3.10** (via Homebrew):
   ```bash
   brew install python@3.10
   ```

2. **Create the virtual environment and install dependencies:**
   ```bash
   /opt/homebrew/opt/python@3.10/bin/python3.10 -m venv venv
   ./venv/bin/pip install pip==24.0                # omegaconf 2.0.6 needs pip <= 24.0
   ./venv/bin/pip install "cython<3" "numpy==1.23.5" "setuptools<81" wheel
   grep -v "^fairseq" requirements.txt > /tmp/req.txt
   ./venv/bin/pip install -r /tmp/req.txt
   # fairseq's PyPI sdist is missing source files; install from the git tag.
   # The CXXFLAGS work around a clang strictness error in torch 2.3 headers.
   CFLAGS="-Wno-invalid-specialization" CXXFLAGS="-Wno-invalid-specialization" \
     ./venv/bin/pip install "git+https://github.com/facebookresearch/fairseq.git@v0.12.2" --no-build-isolation
   ./venv/bin/pip install -r requirements_gui.txt
   ```

3. **Download models** (required — the build bundles these into the app):
   ```bash
   ./venv/bin/python download_models.py
   mkdir -p so-vits-svc/so-vits-svc-4.1-Stable/pretrain
   curl -L -o so-vits-svc/so-vits-svc-4.1-Stable/pretrain/checkpoint_best_legacy_500.pt \
     'https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt'
   ```

## Building, signing, and packaging

```bash
./build_mac.sh
```

That script:
- builds `dist/ai_choir.app` with PyInstaller (`ai_choir.spec`)
- signs every binary during the build with your Developer ID
  (auto-detected from the keychain; override with `CODESIGN_IDENTITY`)
- creates and signs `dist/ai_choir.dmg` (plain `hdiutil`, no extra tools needed)
- optionally notarizes if `NOTARY_PROFILE` is set (see script header)

For an unsigned dev build: `CODESIGN_IDENTITY="" ./build_mac.sh`

## Packaging choices

The voice models (~3.7 GB) and hubert speech encoder (~190 MB) **are bundled
inside the app**, so the result is a single self-contained DMG (~4 GB) that
can be distributed directly — no first-launch downloads, no reliance on
Google Drive / Hugging Face URLs staying alive. `models/` and the hubert
checkpoint must exist in the source tree before building (step 3 above).

Other deliberate choices, so future-you doesn't re-learn them the hard way:

- **No ffmpeg.** The audio pipeline is WAV end-to-end (so-vits-svc is invoked
  with `-wf wav`, pydub only touches WAV). Do not reintroduce MP3 anywhere in
  the pipeline or the packaged app will break on machines without ffmpeg.
- **Signing happens inside PyInstaller** (`codesign_identity` in the spec),
  which signs nested binaries inside-out. Do not use `codesign --deep` on the
  finished bundle — that's what kept failing before.
- **Hardened runtime entitlements** live in `entitlements.plist`
  (unsigned executable memory for numba's JIT, library validation disabled
  for the bundled third-party dylibs).
- `--onedir` mode only. `--onefile` unpacks gigabytes on every launch and
  breaks signing.
- **`rthook_site_builtins.py` is load-bearing.** fairseq 0.12.2 accidentally
  uses the builtin `help` as a dict key (`metadata={help: ...}` in
  `fairseq/dataclass/configs.py`). That builtin only exists because of the
  `site` module, which PyInstaller skips — so frozen apps crash with
  `NameError: name 'help' is not defined` unless the runtime hook restores it.

## Notarization (recommended for distribution)

Without notarization, recipients must right-click > Open the first time.
One-time credential setup:
```bash
xcrun notarytool store-credentials ai-choir \
  --apple-id <your-apple-id> --team-id JY7MWPBBYW --password <app-specific-password>
```
Then build with:
```bash
NOTARY_PROFILE=ai-choir ./build_mac.sh
```

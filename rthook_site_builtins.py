"""PyInstaller runtime hook.

PyInstaller skips the `site` module, so site builtins like `help` are missing
in the frozen app. fairseq 0.12.2 has a bug (`metadata={help: ...}` in
fairseq/dataclass/configs.py EMAConfig — the builtin instead of the string
"help") that only works when `help` exists. Restore it before app imports run.
"""
import builtins

if not hasattr(builtins, 'help'):
    try:
        import _sitebuiltins
        builtins.help = _sitebuiltins._Helper()
    except Exception:
        builtins.help = lambda *args, **kwargs: None

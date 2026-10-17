import subprocess
import sys
import tempfile
from pathlib import Path

TIMEOUT = 15
MAX_OUTPUT = 20_000


def run_code(code: str, timeout: int = TIMEOUT) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "snippet.py"
        script.write_text(code)
        try:
            p = subprocess.run(
                [sys.executable, str(script)],
                cwd=tmp, capture_output=True, text=True, timeout=timeout,
                stdin=subprocess.DEVNULL,
            )
            return {"stdout": p.stdout[:MAX_OUTPUT], "stderr": p.stderr[:MAX_OUTPUT],
                    "returncode": p.returncode, "timed_out": False}
        except subprocess.TimeoutExpired as e:
            return {"stdout": (e.stdout or b"").decode(errors="replace")[:MAX_OUTPUT]
                    if isinstance(e.stdout, bytes) else (e.stdout or ""),
                    "stderr": f"Execution timed out after {timeout}s.",
                    "returncode": -1, "timed_out": True}
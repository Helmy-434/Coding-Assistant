import ast
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

TIMEOUT = 15
MAX_OUTPUT = 20_000
PIP_TIMEOUT = 120

# Import names that do not match their PyPI distribution names.
PACKAGE_NAMES = {
    "cv2": "opencv-python",
    "dotenv": "python-dotenv",
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
}


def _requested_imports(code: str) -> set[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imports.add(node.module.split(".")[0])
    return imports


def _install_missing_dependencies(code: str, timeout: int = PIP_TIMEOUT) -> str | None:
    missing = sorted(
        module for module in _requested_imports(code)
        if importlib.util.find_spec(module) is None
    )
    if not missing:
        return None

    packages = [PACKAGE_NAMES.get(module, module) for module in missing]
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", *packages],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return f"Dependency installation timed out after {timeout} seconds: {', '.join(packages)}"
    except OSError as error:
        return f"Could not start dependency installation: {error}"

    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        return f"Could not install dependencies ({', '.join(packages)}): {details[:MAX_OUTPUT]}"
    return None


def run_code(code: str, timeout: int = TIMEOUT) -> dict:
    dependency_error = _install_missing_dependencies(code)
    if dependency_error:
        return {
            "stdout": "",
            "stderr": dependency_error,
            "returncode": -1,
            "timed_out": False,
        }

    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "snippet.py"
        script.write_text(code, encoding="utf-8")
        try:
            p = subprocess.run(
                [sys.executable, str(script)],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=timeout,
                stdin=subprocess.DEVNULL,
                encoding="utf-8",
                errors="replace",
            )
            return {
                "stdout": p.stdout[:MAX_OUTPUT],
                "stderr": p.stderr[:MAX_OUTPUT],
                "returncode": p.returncode,
                "timed_out": False,
            }
        except subprocess.TimeoutExpired as e:
            stdout_str = e.stdout or ""
            if isinstance(stdout_str, bytes):
                stdout_str = stdout_str.decode(errors="replace")
            return {
                "stdout": stdout_str[:MAX_OUTPUT],
                "stderr": f"Execution timed out after {timeout}s.",
                "returncode": -1,
                "timed_out": True,
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "timed_out": False,
            }
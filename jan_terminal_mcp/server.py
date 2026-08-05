"""
Jan Terminal MCP Server
Exposes shell, git, file system, and code execution tools to Jan AI via MCP.
"""

import asyncio
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

from mcp.server.mcpserver import MCPServer

server = MCPServer("jan-terminal")

# ── Safety blocklist ───────────────────────────────────────────────────────────

BLOCKLIST = [
    "reg delete", "reg add", "regedit",
    "remove-itemproperty", "set-itemproperty",
    "format-volume", "format c:", "format d:",
    "rd /s", "rmdir /s",
    "del /f /s", "del /q /s",
    "rm -rf", "remove-item -recurse -force c:\\",
    "bcdedit", "diskpart",
    "net user", "net localgroup",
    "shutdown", "restart-computer",
]

def _is_dangerous(command: str) -> tuple[bool, str]:
    low = command.lower()
    for pattern in BLOCKLIST:
        if pattern in low:
            return True, pattern
    return False, ""


def _format_output(label: str, cmd: str, out: str, lang: str = "") -> str:
    out = out.strip() if out else "(no output)"
    prompt = "bash"
    # Use language-specific prompt style
    lang_prompts = {
        "python": "python",
        "javascript": "javascript",
        "typescript": "typescript",
        "java": "java",
        "cpp": "cpp",
        "go": "go",
        "rust": "rust",
        "ruby": "ruby",
        "php": "php",
        "r": "r",
    }
    syntax = lang_prompts.get(lang.lower(), "bash")
    return (
        f"```{syntax}\n$ {cmd}\n```\n"
        f"```\n{out}\n```"
    )

# ── Tools ──────────────────────────────────────────────────────────────────────

@server.tool()
def run_shell(command: str, cwd: str = "") -> str:
    """Run a PowerShell command on the user's machine."""
    blocked, pattern = _is_dangerous(command)
    if blocked:
        return f"BLOCKED: dangerous pattern '{pattern}' — will not execute."
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True, text=True,
            cwd=cwd or os.getcwd(), timeout=30
        )
        out = (result.stdout + result.stderr).strip()
        return _format_output("Shell output", command, out[:4000], "bash")
    except subprocess.TimeoutExpired:
        return "ERROR: timed out after 30s"
    except Exception as e:
        return f"ERROR: {e}"


@server.tool()
def git(args: str, cwd: str = "") -> str:
    """Run a git command. args = e.g. 'status', 'log --oneline -10', 'commit -m "fix bug"'"""
    blocked, pattern = _is_dangerous(args)
    if blocked:
        return f"BLOCKED: dangerous pattern '{pattern}'."
    try:
        result = subprocess.run(
            ["git"] + shlex.split(args),
            capture_output=True, text=True,
            cwd=cwd or os.getcwd(), timeout=30
        )
        out = (result.stdout + result.stderr).strip()
        return _format_output("Git output", f"git {args}", out[:4000], "bash")
    except subprocess.TimeoutExpired:
        return "ERROR: timed out after 30s"
    except Exception as e:
        return f"ERROR: {e}"


@server.tool()
def read_file(path: str) -> str:
    """Read the contents of a file on the user's machine."""
    try:
        p = Path(path)
        if not p.exists():
            return f"ERROR: file not found: {path}"
        content = p.read_text(encoding="utf-8", errors="replace")
        if len(content) > 8000:
            content = content[:8000] + "\n\n... (truncated)"
        return _format_output("File contents", path, content)
    except Exception as e:
        return f"ERROR: {e}"


@server.tool()
def write_file(path: str, content: str) -> str:
    """Write or overwrite a file on the user's machine. After writing code, use run_file to execute it — do NOT also call run_code with the same code."""
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"OK: wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"ERROR: {e}"


@server.tool()
def list_dir(path: str) -> str:
    """List files and folders in a directory."""
    try:
        p = Path(path)
        if not p.exists():
            return f"ERROR: path not found: {path}"
        items = sorted(p.iterdir())
        lines = [("DIR  " if i.is_dir() else "FILE ") + i.name for i in items]
        out = "\n".join(lines) if lines else "(empty directory)"
        return _format_output("Directory listing", path, out, "bash")
    except Exception as e:
        return f"ERROR: {e}"


@server.tool()
def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Edit a file by replacing old_text with new_text. Use this to fix errors instead of rewriting the whole file."""
    try:
        p = Path(path)
        if not p.exists():
            return f"ERROR: file not found: {path}"
        content = p.read_text(encoding="utf-8", errors="replace")
        if old_text not in content:
            return f"ERROR: text not found in {path}"
        updated = content.replace(old_text, new_text, 1)
        p.write_text(updated, encoding="utf-8")
        return f"OK: edited {path}"
    except Exception as e:
        return f"ERROR: {e}"


@server.tool()
def run_file(path: str, language: str = "") -> str:
    """Run an already-existing file. Use this after write_file — avoids writing the code twice.
    Language is auto-detected from extension if not provided.
    """
    p = Path(path)
    if not p.exists():
        return f"ERROR: file not found: {path}"

    ext_map = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".java": "java", ".cpp": "cpp", ".cs": "csharp",
        ".go": "go", ".rs": "rust", ".rb": "ruby",
        ".php": "php", ".r": "r", ".kt": "kotlin",
        ".swift": "swift", ".m": "matlab",
    }
    lang = language.lower() if language else ext_map.get(p.suffix.lower(), "")
    if not lang:
        return f"ERROR: cannot detect language from '{p.suffix}'. Pass language= explicitly."

    work = str(p.parent)
    src = str(p)

    def run(*cmd):
        r = subprocess.run(list(cmd), capture_output=True, text=True, cwd=work, timeout=30)
        return (r.stdout + r.stderr).strip(), r.returncode

    try:
        if lang == "python":
            out, _ = run(sys.executable, src)
        elif lang == "javascript":
            out, _ = run("node", src)
        elif lang == "typescript":
            out, rc = run("npx", "--yes", "tsx", src)
            if rc != 0:
                out, _ = run("npx", "--yes", "ts-node", src)
        elif lang == "java":
            out, rc = run("javac", src)
            if rc != 0:
                return f"COMPILE ERROR:\n{out}"
            out, _ = run("java", "-cp", work, p.stem)
        elif lang == "cpp":
            exe = src.replace(".cpp", ".exe")
            out, rc = run("g++", src, "-o", exe, "-std=c++17")
            if rc != 0:
                return f"COMPILE ERROR:\n{out}"
            out, _ = run(exe)
            try: os.unlink(exe)
            except: pass
        elif lang == "csharp":
            out, _ = run("dotnet-script", src)
        elif lang == "go":
            out, _ = run("go", "run", src)
        elif lang == "rust":
            exe = src.replace(".rs", ".exe")
            out, rc = run("rustc", src, "-o", exe)
            if rc != 0:
                return f"COMPILE ERROR:\n{out}"
            out, _ = run(exe)
            try: os.unlink(exe)
            except: pass
        elif lang == "ruby":
            out, _ = run("ruby", src)
        elif lang == "php":
            out, _ = run("php", src)
        elif lang == "r":
            out, _ = run("Rscript", src)
        elif lang == "kotlin":
            jar = src.replace(".kt", ".jar")
            out, rc = run("kotlinc", src, "-include-runtime", "-d", jar)
            if rc != 0:
                return f"COMPILE ERROR:\n{out}"
            out, _ = run("java", "-jar", jar)
            try: os.unlink(jar)
            except: pass
        elif lang == "swift":
            out, _ = run("swift", src)
        else:
            return f"ERROR: unsupported language '{lang}'"

        return _format_output(f"{lang.title()} output", path, out[:4000], lang)

    except subprocess.TimeoutExpired:
        return "ERROR: timed out after 30s"
    except FileNotFoundError as e:
        return f"ERROR: runtime not found — is {lang} installed? ({e})"
    except Exception as e:
        return f"ERROR: {e}"


@server.tool()
def run_code(language: str, code: str, cwd: str = "") -> str:
    """Execute a code snippet directly without saving to disk. Use for quick one-off runs.
    If you already wrote the code with write_file, use run_file instead to avoid writing twice.
    Supported: python, javascript, typescript, java, cpp, csharp, go, rust, ruby, php, r, kotlin, swift, matlab
    """
    lang = language.lower().strip().replace(" ", "").replace("#", "sharp").replace("+", "p")
    aliases = {
        "js": "javascript", "node": "javascript", "nodejs": "javascript",
        "ts": "typescript",
        "c": "cpp", "cplusplus": "cpp",
        "cs": "csharp", "dotnet": "csharp",
        "golang": "go",
        "rb": "ruby",
        "rs": "rust",
        "kt": "kotlin",
        "rscript": "r",
    }
    lang = aliases.get(lang, lang)

    extensions = {
        "python": ".py", "javascript": ".js", "typescript": ".ts",
        "java": ".java", "cpp": ".cpp", "csharp": ".cs",
        "go": ".go", "rust": ".rs", "ruby": ".rb",
        "php": ".php", "r": ".R", "kotlin": ".kt", "swift": ".swift",
        "matlab": ".m",
    }
    ext = extensions.get(lang, ".txt")
    src = None

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False, encoding="utf-8") as f:
            f.write(code)
            src = f.name

        return run_file(src, lang)

    except Exception as e:
        return f"ERROR: {e}"
    finally:
        try:
            if src: os.unlink(src)
        except: pass


@server.tool()
def run_python(code: str, cwd: str = "") -> str:
    """Execute Python code directly and return the output."""
    return run_code("python", code, cwd)


@server.tool()
def run_cpp(code: str, cwd: str = "") -> str:
    """Compile and run C++ code. Returns compiler errors or program output."""
    return run_code("cpp", code, cwd)


def main():
    asyncio.run(server.run_stdio_async())


if __name__ == "__main__":
    main()

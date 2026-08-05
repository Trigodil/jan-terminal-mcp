# jan-terminal-mcp

A [Model Context Protocol (MCP)](https://www.jan.ai/docs/desktop/mcp) server for [Jan AI](https://jan.ai) that gives your local model real terminal access — shell commands, git, file read/write, and directory listing.

Every operation shows a **user approval prompt** before anything runs on your machine.


## Tools

| Tool | Description |
|------|-------------|
| `run_shell` | Run any PowerShell command |
| `git` | Run git commands in any repo |
| `read_file` | Read any file's contents |
| `write_file` | Write or overwrite a file |
| `list_dir` | List files and folders in a directory |
| `edit_file` | Replace a specific substring in a file — use this to fix errors instead of rewriting the whole file |
| `run_python` | Execute Python code directly and return output |
| `run_cpp` | Compile and run C++ code (g++ or MSVC), returns errors + output |
| `run_code` | Execute code in **any** language — Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, Ruby, PHP, R, Kotlin, Swift, MATLAB |

## Fine-tuned model

[AItrainer1/jancoder-4b-gguf](https://huggingface.co/AItrainer1/jancoder-4b-gguf) - Jan-code-4b fine tuned on tool-use conversations via QLoRA. Drop the GGUF into Jan and it reliably calls tools instead of explaining them.

The Kaggle training notebook is at [`kaggle_finetune.ipynb`](kaggle_finetune.ipynb).

## Install

```bash
pip install jan-terminal-mcp
```

## Setup in Jan AI

1. Open Jan → **Settings → MCP Servers**
2. Click **Add** and paste this config:

```json
{
  "jan-terminal": {
    "command": "jan-terminal-mcp",
    "args": [],
    "env": {},
    "active": true
  }
}
```

Or edit `%APPDATA%\Jan\data\mcp_config.json` directly and add the block above inside `"mcpServers"`.

3. Restart Jan — the server appears as **Jan-Terminal** with a green dot.

## How it works

When Jan's model calls a tool, a Windows dialog appears asking for your approval **before** anything runs:

- `run_shell` / `git` → warning popup showing the exact command
- `write_file` → warning popup with a content preview
- `read_file` / `list_dir` → info popup

Click **Allow** to proceed or **Deny** to cancel. Jan's own built-in approval UI also fires, so you get a double layer of confirmation.

## Requirements

- Windows (uses native Win32 dialog for approval prompts)
- Python 3.10+
- Jan AI v0.7.9+
- `pip install mcp>=2.0.0`

## License

MIT

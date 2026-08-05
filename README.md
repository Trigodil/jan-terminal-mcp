# jan-terminal-mcp

**Jan AI has no native terminal or code execution. This gives it that.**

An [MCP](https://www.jan.ai/docs/desktop/mcp) server that gives your local Jan model real hands on your machine — run shell commands, execute code in 14 languages, read/write files, and use git. All locally, all private.

Includes a [fine-tuned 4B model](#fine-tuned-model) trained specifically to call these tools reliably instead of just describing what it would do.


## Tools

| Tool | Description |
|------|-------------|
| `run_shell` | Run any PowerShell command |
| `git` | Run git commands in any repo |
| `read_file` | Read any file's contents |
| `write_file` | Write or overwrite a file |
| `list_dir` | List files and folders in a directory |
| `edit_file` | Replace a specific substring in a file — smarter than rewriting the whole thing |
| `run_python` | Execute Python code directly and return output |
| `run_cpp` | Compile and run C++ code (g++), returns errors + output |
| `run_code` | Execute code in **any** language — Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, Ruby, PHP, R, Kotlin, Swift, MATLAB |

## Fine-tuned model

[AItrainer1/jancoder-4b-gguf](https://huggingface.co/AItrainer1/jancoder-4b-gguf) — a 4B model fine-tuned via QLoRA on tool-use conversations generated specifically for this tool schema.

Stock models at this size tend to describe what they'd do rather than actually calling tools. This model was trained to call them correctly and consistently.

Drop the GGUF into Jan and it works out of the box with this MCP server.

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

## Requirements

- Windows (PowerShell required for `run_shell`)
- Python 3.10+
- Jan AI v0.7.9+
- `pip install mcp>=2.0.0`

##Bugs

Report bugs and stuff to [ISSUE](https://github.com/Trigodil/jan-terminal-mcp/tree/main/.github/ISSUE_TEMPLATE)

## License

MIT

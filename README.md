# llm-fuse

`llm-fuse` is a command‑line tool designed to help you quickly generate an aggregated text file (or multiple files when chunking is enabled) from numerous files within a repository. This output can then be pasted into a large language model (LLM) prompt to provide context from multiple source files.

## Features

- **Local Directory Scanning:** Recursively scan a local directory for files.
- **Git‑tracked Files Option:** Optionally limit scanning to Git‑tracked files.
- **Remote Repository Cloning:** Clone and process a Git repository from GitHub, GitLab, or any other Git‑based service.
- **File Filtering:** Include or exclude files using regular expressions.
- **Token Counting:** Roughly estimate token counts (approx. 1 token per 4 characters) for each file.
- **Aggregated Output:** Generates a primary output file with a summary header, file system diagram, and individual file sections.
- **Content Chunking:** Automatically splits file content into manageable chunks if it exceeds a specified maximum token threshold (via the `--max-tokens` option). The primary output file (group 1) includes the summary and file tree, while additional chunks are written to separate output files.

## Examples

For examples of what the script can output have a look at `EXAMPLE_OUTPUT` - the file was generated by running:

```bash
llm-fuse --git --repo https://github.com/antonbelev/llm-fuse
```

## Installation

To install `llm-fuse` globally, follow these steps:

1. Clone the Repository:
Open your terminal and run:
```bash
git clone https://github.com/antonbelev/llm-fuse.git
cd llm-fuse
```

2. Choose an Installation Method

You can install `llm-fuse` using one of the following methods:

### Option 1: Global Installation with pip

You can install the package globally (or for your user) with pip. Note that if you use a Homebrew‑managed Python on macOS, you might encounter restrictions installing system‑wide packages. To install for your user, run:

```bash
pip3 install --user . 
```

This will install the command‑line tool `llm-fuse` into your user’s local bin directory (typically `~/.local/bin`). Make sure that directory is added to your PATH.

### Option 2: Installation with pipx (Recommended)

`pipx` allows you to install and run Python CLI applications in isolated environments without interfering with your system Python. This is especially useful if you want the command to be available globally without activating a virtual environment.

1. Install pipx (if not already installed):

```bash
brew install pipx
brew upgrade pipx
```

2. Install `llm-fuse` with pipx:

From the root of your repository, run:
```bash
pipx install .
```

pipx will create an isolated environment for the tool and install its CLI command. The command is typically named `llm-fuse` (as defined in the entry point).

3. Ensure Your `PATH` is Set Up (following instructions are For macOS zsh specific)
   
By default, pipx installs commands in `~/.local/bin`. To ensure this directory is included in your system's `PATH`, run:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

This command does the following:

- Appends export `PATH="$HOME/.local/bin:$PATH"` to your `~/.zshrc` file.
- Immediately applies the changes by running source `~/.zshrc`.

Using `pipx` is recommended because it keeps the CLI application isolated from your system packages while still making the command available globally.

## Usage

Too see all options run:

```bash
llm-fuse --help
```

### Processing a Local Directory

```bash
# Process the current directory and output to output.txt
llm-fuse

# Process a specific directory and only include Python files
llm-fuse /path/to/repo --include "\.py$"

# Exclude test files
llm-fuse /path/to/repo --exclude "test"

# Use only Git‑tracked files (if in a Git repository)
llm-fuse /path/to/repo --git
```

### Processing a Remote Repository

```bash
# Process a GitHub repository using the default branch
llm-fuse --repo https://github.com/user/repo.git

# Process a GitLab repository specifying a branch
llm-fuse --repo https://gitlab.com/user/repo.git --branch develop
```

### Enabling Content Chunking
If you have very large files, you can specify a maximum token threshold using the --max-tokens option. Files exceeding this threshold will be split into chunks, with additional output files created for subsequent chunks (only the primary output file includes the summary header and file system diagram).

```bash
# Process a repository and split large files into chunks of 4000 tokens
llm-fuse /path/to/repo --max-tokens 4000
```

The output is written to `output.txt` by default. You can specify a different file name with the `--output` option.

## Contributing
Contributions are welcome! Feel free to open issues or submit pull requests.

## Local Development

To run the unit tests:
```bash
python3 -m unittest discover -s tests
```

## License
This project is licensed under the MIT License. See the LICENSE file for details.
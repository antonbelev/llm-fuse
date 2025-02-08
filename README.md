# LLM Context Aggregator

LLM Context Aggregator is a command‑line tool designed to help you quickly generate a single, aggregated text file from multiple files within a repository. This file can then be pasted into a large language model (LLM) prompt to provide context from multiple source files.

## Features

- **Local Directory Scanning:** Recursively scan a local directory for files.
- **Git-tracked Files Option:** Optionally limit scanning to Git‑tracked files.
- **Remote Repository Cloning:** Clone and process a Git repository from GitHub, GitLab, or any other Git-based service.
- **File Filtering:** Include or exclude files using regular expressions.
- **Token Counting:** Roughly estimate token counts (approx. 1 token per 4 characters) for each file.
- **Aggregated Output:** Generates a single output file with a summary header and individual file sections.

## Installation

Clone the repository and install via pip (or use the provided setup script):

```bash
git clone https://github.com/yourusername/llm-context-aggregator.git
cd llm-context-aggregator
pip3 install .
```

This will install the command-line tool `llm_context_aggregator` that you can run from anywhere.

## Usage
### Processing a Local Directory

```bash
# Process the current directory and output to output.txt
llm_context_aggregator

# Process a specific directory and only include Python files
llm_context_aggregator /path/to/repo --include "\.py$"

# Exclude test files
llm_context_aggregator /path/to/repo --exclude "test"

# Use only Git-tracked files (if in a Git repository)
llm_context_aggregator /path/to/repo --git
```

### Processing a Remote Repository

```bash
# Process a GitHub repository using the default branch
llm_context_aggregator --repo https://github.com/user/repo.git

# Process a GitLab repository specifying a branch
llm_context_aggregator --repo https://gitlab.com/user/repo.git --branch develop
```
The output is written to `output.txt` by default. You can specify another file with the `--output` option.

## Contributing
Contributions are welcome! Feel free to open issues or submit pull requests.

## License
This project is licensed under the MIT License. See the LICENSE file for details.


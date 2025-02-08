#!/usr/bin/env python3
"""
llm-fuse
----------------------
A tool to help aggregate source files (or any text files) into one or more output files
that you can paste into an LLM prompt to provide context. This version supports:

- Scanning a local directory (or only Git-tracked files via --git)
- Cloning a remote Git repository (GitHub, GitLab, etc.) via URL with --repo
- Optional branch specification using --branch
- Recursive file scanning with include/exclude filtering (via regex)
- Rough token counting (approx. 1 token per 4 characters)
- Automatic chunking of file content if it exceeds a specified token threshold (--max-tokens)
- Producing one aggregated output file with a header summary and file system diagram
  for all non-chunked and first-chunk content, plus separate output files for subsequent chunks.
  
Usage:
    # Process a local directory (current directory by default)
    llm-fuse [directory] [--output OUTPUT] [--include REGEX] [--exclude REGEX] [--git]

    # Process only JavaScript files in a repository:
    llm-fuse --repo https://gitlab.com/antonbelev/beblob --include ".*\\.js$"

Notes:
  - When using --repo, the repository is cloned into a temporary directory,
    processed, and then removed after generating the output files.
  - In the aggregated output file, file paths are rendered relative to the repository root,
    always prefixed with "./" (e.g. "./webpack.config.js", "./src/js/main.js").
  - The token count is estimated using a simple heuristic of 1 token per 4 characters.
  - Files exceeding the --max-tokens threshold are split into manageable chunks.
  - Only the first output file (group 1) includes the summary and file system diagram.
"""

import os
import re
import math
import argparse
import subprocess
import tempfile
import shutil
import sys
from typing import List, Tuple, Optional

def approximate_token_count(text: str) -> int:
    """
    Estimate the token count using a simple heuristic: roughly one token per 4 characters.
    """
    return math.ceil(len(text) / 4)

def is_text_file(file_path: str) -> bool:
    """
    Attempt to read a small portion of the file with UTF-8 encoding.
    If successful, assume it is a text file; otherwise skip binary or unreadable files.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except Exception:
        return False

def get_git_tracked_files(directory: str) -> Optional[List[str]]:
    """
    If the directory is a Git repository, use 'git ls-files' to return a list of tracked files.
    Returns None if there is an error (or if it isn’t a git repo).
    """
    try:
        output = subprocess.check_output(
            ["git", "ls-files"],
            cwd=directory,
            text=True
        )
        files = output.splitlines()
        return files
    except Exception:
        return None

def collect_files(directory: str, include_regex: Optional[str],
                  exclude_regex: Optional[str], git_only: bool) -> List[str]:
    """
    Collect a list of file paths based on the provided options.
    If git_only is True and the directory is a git repository, only Git-tracked files are considered.
    Otherwise, all files under the directory (recursively) are considered.
    Filtering via include/exclude regex is applied on the full file path.
    """
    file_paths = []
    if git_only:
        git_files = get_git_tracked_files(directory)
        if git_files:
            # git ls-files returns paths relative to the repo root.
            file_paths = [os.path.join(directory, f) for f in git_files]
        else:
            print("Warning: Not a Git repository or unable to retrieve Git files. Falling back to a full directory scan.")
    if not file_paths:
        for root, _, files in os.walk(directory):
            for file in files:
                file_paths.append(os.path.join(root, file))
    # Apply include/exclude filters if specified
    filtered_paths = []
    for path in file_paths:
        if include_regex and not re.search(include_regex, path):
            continue
        if exclude_regex and re.search(exclude_regex, path):
            continue
        filtered_paths.append(path)
    return filtered_paths

def process_files(file_paths: List[str], max_tokens: Optional[int] = None) -> Tuple[List[dict], int]:
    """
    Process the list of files. For each file determined to be a text file,
    read its content and compute its approximate token count.
    If max_tokens is provided and the file's token count exceeds this threshold,
    split the content into chunks.
    
    Returns a list of dictionaries (each containing file path, content, tokens, and, if chunked,
    chunk index/total chunks) and the total token count.
    """
    files_data = []
    total_tokens = 0
    for file_path in file_paths:
        if not is_text_file(file_path):
            continue
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tokens = approximate_token_count(content)
            if max_tokens is not None and tokens > max_tokens:
                # Estimate maximum characters per chunk (approximation: 1 token ≈ 4 characters)
                max_chars = max_tokens * 4
                chunks = [content[i:i+max_chars] for i in range(0, len(content), max_chars)]
                for idx, chunk in enumerate(chunks):
                    tokens_chunk = approximate_token_count(chunk)
                    total_tokens += tokens_chunk
                    files_data.append({
                        "path": file_path,
                        "content": chunk,
                        "tokens": tokens_chunk,
                        "chunk_index": idx + 1,
                        "total_chunks": len(chunks)
                    })
            else:
                total_tokens += tokens
                files_data.append({
                    "path": file_path,
                    "content": content,
                    "tokens": tokens
                })
        except Exception as e:
            print(f"Skipping file '{file_path}' due to error: {e}")
    return files_data, total_tokens

def build_tree_from_paths(paths: List[str]) -> dict:
    """
    Given a list of relative file paths, build a nested dictionary representing
    the file system tree.
    Directories are keys with dictionary values; files are keys with a value of None.
    """
    tree = {}
    for path in paths:
        parts = path.split(os.sep)
        node = tree
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                # Last part: a file.
                node[part] = None
            else:
                if part not in node:
                    node[part] = {}
                node = node[part]
    return tree

def render_tree(tree: dict, prefix: str = "") -> List[str]:
    """
    Render the tree dictionary into a list of strings representing a tree diagram.
    Directories are printed first and then files, using Unicode tree drawing characters.
    """
    lines = []
    # Sort: directories first, then files; both alphabetically.
    keys = sorted(tree.keys(), key=lambda k: (tree[k] is None, k.lower()))
    for i, key in enumerate(keys):
        is_last = i == len(keys) - 1
        connector = "└── " if is_last else "├── "
        if tree[key] is None:
            # It's a file.
            lines.append(prefix + connector + key)
        else:
            # It's a directory.
            lines.append(prefix + connector + key)
            new_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(render_tree(tree[key], new_prefix))
    return lines

def write_output_files(files_data: List[dict], total_tokens: int, output_path: str,
                       base_dir: str, display_base_dir: Optional[str] = None) -> None:
    """
    Write the aggregated content to one or more output files.
    
    - All file sections that are non-chunked or are the first chunk (chunk_index == 1)
      are grouped together into the main output file (using the provided output_path).
      This file includes a summary header and file system diagram.
      
    - For file sections with chunk_index > 1, they are grouped by chunk index and
      written to separate output files (named by appending _<chunk_index> to the base name).
    """
    # Group the file sections by chunk index; treat missing 'chunk_index' as 1.
    groups = {}
    for file_data in files_data:
        chunk = file_data.get("chunk_index", 1)
        groups.setdefault(chunk, []).append(file_data)
    
    # Process each group in ascending order.
    for chunk_index in sorted(groups.keys()):
        group = groups[chunk_index]
        # Determine output file name.
        if chunk_index == 1:
            out_file = output_path
        else:
            base, ext = os.path.splitext(output_path)
            out_file = f"{base}_{chunk_index}{ext}"
        
        try:
            with open(out_file, 'w', encoding='utf-8') as f:
                # Only group 1 gets the summary header and file system diagram.
                if chunk_index == 1:
                    header = (
                        "LLM Fuse Aggregation Output\n"
                        "===============================\n"
                        f"Base directory: {display_base_dir if display_base_dir is not None else base_dir}\n"
                        f"Total files (or chunks) processed: {len(files_data)}\n"
                        f"Total approximate tokens: {total_tokens}\n\n"
                    )
                    f.write(header)
                    relative_paths = [os.path.relpath(fd['path'], base_dir) for fd in files_data]
                    tree = build_tree_from_paths(relative_paths)
                    diagram_lines = render_tree(tree)
                    f.write("File System Diagram:\n")
                    f.write("---------------------\n")
                    for line in diagram_lines:
                        f.write(line + "\n")
                    f.write("\n")
                # Write each file section in the group.
                for file_data in group:
                    rel_path = os.path.relpath(file_data['path'], base_dir)
                    relative_path = "./" + rel_path.replace("\\", "/")
                    if "chunk_index" in file_data:
                        # If it was chunked, display chunk info.
                        if file_data['chunk_index'] > 1:
                            file_header = (
                                "--------------------------------------------------\n"
                                f"File: {relative_path} (Chunk {file_data['chunk_index']} of {file_data['total_chunks']})\n"
                                f"Approx. tokens: {file_data['tokens']}\n"
                                "--------------------------------------------------\n"
                            )
                        else:
                            file_header = (
                                "--------------------------------------------------\n"
                                f"File: {relative_path}\n"
                                f"Approx. tokens: {file_data['tokens']}\n"
                                "--------------------------------------------------\n"
                            )
                    else:
                        file_header = (
                            "--------------------------------------------------\n"
                            f"File: {relative_path}\n"
                            f"Approx. tokens: {file_data['tokens']}\n"
                            "--------------------------------------------------\n"
                        )
                    f.write(file_header)
                    f.write(file_data['content'])
                    f.write("\n\n")
            print(f"Output written to: {out_file}")
        except Exception as e:
            print(f"Error writing output file '{out_file}': {e}")
            sys.exit(1)

def clone_repo(repo_url: str, branch: Optional[str] = None) -> str:
    """
    Clone the Git repository (GitHub, GitLab, etc.) into a temporary directory.
    If a branch is specified, clone that branch.
    Returns the path to the temporary directory containing the cloned repository.
    """
    tmp_dir = tempfile.mkdtemp(prefix="git_repo_")
    clone_cmd = ["git", "clone", "--depth", "1"]
    if branch:
        clone_cmd.extend(["--branch", branch])
    clone_cmd.extend([repo_url, tmp_dir])
    try:
        print(f"Cloning repository {repo_url} into temporary directory...")
        subprocess.check_call(clone_cmd)
        return tmp_dir
    except subprocess.CalledProcessError as e:
        shutil.rmtree(tmp_dir)
        raise RuntimeError(f"Error cloning repository: {e}")

def extract_repo_name(repo_url: str) -> str:
    """
    Extract the repository name from the repository URL.
    For example, from 'https://gitlab.com/antonbelev/beblob' it returns 'beblob'.
    Removes any trailing '.git' if present.
    """
    name = repo_url.rstrip('/').split('/')[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name

def main():
    parser = argparse.ArgumentParser(
        description="Aggregate file contents into one or more files for LLM context."
    )
    # Add a version flag
    parser.add_argument('--version', action='version', version='llm-fuse 0.1.0')
    
    # Local directory argument (positional) is ignored if --repo is provided.
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Local directory to scan. Defaults to current directory. Ignored if --repo is provided."
    )
    parser.add_argument(
        "--include",
        type=str,
        help="Regex pattern to include files (applied to the full file path). For example: '.*\\.js$'"
    )
    parser.add_argument(
        "--exclude",
        type=str,
        help="Regex pattern to exclude files (applied to the full file path). For example: '.*(test|spec)\\.js$'"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output.txt",
        help="Output file name for the primary (first-chunk) output. Defaults to 'output.txt'."
    )
    parser.add_argument(
        "--git",
        action="store_true",
        help="If set, only include Git-tracked files (if available)."
    )
    parser.add_argument(
        "--repo",
        type=str,
        help="Git repository URL to clone and process (supports GitHub, GitLab, etc.)."
    )
    parser.add_argument(
        "--branch",
        type=str,
        default=None,
        help="Specify branch to clone from the repository (if not provided, the default branch is used)."
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Maximum token threshold per chunk. Files exceeding this threshold will be split into manageable chunks."
    )
    args = parser.parse_args()

    temp_repo = False
    display_base_dir = None
    if args.repo:
        try:
            repo_clone_dir = clone_repo(args.repo, args.branch)
        except RuntimeError as e:
            print(e)
            sys.exit(1)
        items = os.listdir(repo_clone_dir)
        subdirs = [os.path.join(repo_clone_dir, item) for item in items if os.path.isdir(os.path.join(repo_clone_dir, item))]
        if len(subdirs) == 1:
            base_dir = os.path.normpath(os.path.abspath(subdirs[0]))
        else:
            base_dir = os.path.normpath(os.path.abspath(repo_clone_dir))
        repo_name = extract_repo_name(args.repo)
        display_base_dir = "./" + repo_name
        print(f"Processing cloned repository: {display_base_dir}")
        temp_repo = True
    else:
        directory = os.path.normpath(os.path.abspath(args.directory))
        if not os.path.isdir(directory):
            print(f"Error: The specified directory '{directory}' does not exist or is not accessible.")
            sys.exit(1)
        base_dir = directory
        display_base_dir = base_dir
        print(f"Scanning local directory: {base_dir}")

    file_paths = collect_files(base_dir, args.include, args.exclude, args.git)
    if not file_paths:
        print("Error: No files found matching the specified criteria.")
        sys.exit(1)
    print(f"Found {len(file_paths)} files after filtering.")

    files_data, total_tokens = process_files(file_paths, max_tokens=args.max_tokens)
    print(f"Processed {len(files_data)} file sections. Total approximate tokens: {total_tokens}")

    write_output_files(files_data, total_tokens, args.output, base_dir, display_base_dir)

    if temp_repo:
        try:
            shutil.rmtree(os.path.dirname(base_dir) if base_dir != os.path.abspath(repo_clone_dir) else repo_clone_dir)
            print(f"Cleaned up temporary repository directory: {repo_clone_dir}")
        except Exception as e:
            print(f"Error cleaning up temporary directory: {e}")

if __name__ == "__main__":
    main()

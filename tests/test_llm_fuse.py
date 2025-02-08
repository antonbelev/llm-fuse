import os
import tempfile
import unittest
import math
import shutil

# Import functions from your module. Adjust the import if your module path differs.
from llm_fuse.main import (
    approximate_token_count,
    is_text_file,
    collect_files,
    process_files,
    build_tree_from_paths,
    render_tree,
    write_output_files
)

class TestLLMFuse(unittest.TestCase):

    def test_approximate_token_count(self):
        # For 4 characters, token count should be 1; for 6 characters, it should be 2.
        self.assertEqual(approximate_token_count("abcd"), 1)
        self.assertEqual(approximate_token_count("abcdef"), 2)

    def test_is_text_file_with_text(self):
        # Create a temporary text file.
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
            tf.write("Hello World")
            filename = tf.name
        try:
            self.assertTrue(is_text_file(filename))
        finally:
            os.remove(filename)

    def test_is_text_file_with_binary(self):
        # Create a temporary binary file.
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tf:
            tf.write(b"\x00\xFF\x00\xFF")
            filename = tf.name
        try:
            self.assertFalse(is_text_file(filename))
        finally:
            os.remove(filename)

    def test_collect_files_with_filters(self):
        # Create a temporary directory with multiple files.
        with tempfile.TemporaryDirectory() as temp_dir:
            file_txt = os.path.join(temp_dir, "file1.txt")
            file_log = os.path.join(temp_dir, "file2.log")
            with open(file_txt, "w") as f:
                f.write("content")
            with open(file_log, "w") as f:
                f.write("more content")
            # Use include filter to only include .txt files.
            files = collect_files(temp_dir, include_regex=r".*\.txt$", exclude_regex=None, git_only=False)
            self.assertIn(file_txt, files)
            self.assertNotIn(file_log, files)

    def test_process_files_without_chunking(self):
        # Create a temporary file that doesn't require chunking.
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
            tf.write("abcd")  # 4 characters, token count = ceil(4/4) = 1
            filename = tf.name
        try:
            files_data, total_tokens = process_files([filename], max_tokens=None)
            self.assertEqual(len(files_data), 1)
            self.assertEqual(total_tokens, 1)
        finally:
            os.remove(filename)

    def test_process_files_with_chunking(self):
        # Create a file with content long enough to require chunking.
        content = "abcdefghij"  # 10 characters, token count = ceil(10/4) = 3
        # Set max_tokens=1 so that the file will be split.
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
            tf.write(content)
            filename = tf.name
        try:
            files_data, total_tokens = process_files([filename], max_tokens=1)
            # With max_tokens=1, maximum characters per chunk = 4.
            # Expect chunks: "abcd", "efgh", "ij"
            self.assertEqual(len(files_data), 3)
            expected_tokens = (approximate_token_count("abcd") +
                               approximate_token_count("efgh") +
                               approximate_token_count("ij"))
            self.assertEqual(total_tokens, expected_tokens)
        finally:
            os.remove(filename)

    def test_build_tree_from_paths(self):
        paths = ["dir1/file1.txt", "dir1/file2.txt", "dir2/file3.txt"]
        tree = build_tree_from_paths(paths)
        expected_tree = {
            "dir1": {"file1.txt": None, "file2.txt": None},
            "dir2": {"file3.txt": None}
        }
        self.assertEqual(tree, expected_tree)

    def test_render_tree(self):
        tree = {
            "dir1": {"file1.txt": None, "file2.txt": None},
            "dir2": {"file3.txt": None}
        }
        lines = render_tree(tree)
        # Check that expected substrings are present in the output.
        self.assertTrue(any("dir1" in line for line in lines))
        self.assertTrue(any("file1.txt" in line for line in lines))
        self.assertTrue(any("dir2" in line for line in lines))
        self.assertTrue(any("file3.txt" in line for line in lines))

    def test_write_output_files(self):
        # Create a dummy files_data list.
        files_data = [
            {"path": "file1.txt", "content": "Hello", "tokens": 2},
            {"path": "file2.txt", "content": "World", "tokens": 2, "chunk_index": 2, "total_chunks": 2}
        ]
        total_tokens = 4
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "output.txt")
            base_dir = temp_dir
            display_base_dir = temp_dir
            write_output_files(files_data, total_tokens, output_path, base_dir, display_base_dir)
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Check that the header and file names appear in the output.
            self.assertIn("LLM Fuse Aggregation Output", content)
            self.assertIn("file1.txt", content)
            self.assertIn("file2.txt", content)

if __name__ == "__main__":
    unittest.main()

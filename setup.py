from setuptools import setup, find_packages

setup(
    name="llm-fuse",
    version="0.1.0",
    description="Aggregate source files for LLM context generation",
    author="Anton Belev",
    author_email="youremail@example.com",
    url="https://github.com/antonbelev/llm-fuse",
    packages=find_packages(),  # This finds all packages in your project.
    entry_points={
        "console_scripts": [
            # This creates a command named `llm-fuse` which points to the main() function
            # in the main module of your package (adjust the module path as necessary).
            "llm-fuse=llm_fuse.main:main",
        ],
    },
    install_requires=[
        # List any dependencies here, for example
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)

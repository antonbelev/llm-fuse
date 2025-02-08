import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="llm_context_aggregator",
    version="0.1.0",
    author="Anton Belev",
    author_email="your.email@example.com",
    description="A tool to aggregate repository files into a single prompt for LLMs.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/llm-context-aggregator",
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": [
            "llm_context_aggregator=llm_context_aggregator.aggregator:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)

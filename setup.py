from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="video-to-nerf",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A GUI application to convert videos to NeRF-compatible datasets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/video-to-nerf",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "paramiko>=2.7.2",
        "pillow>=8.0.0",
        "ffmpeg-python>=0.2.0",
        "numpy>=1.19.0",
    ],
    entry_points={
        "console_scripts": [
            "video-to-nerf=video_to_nerf.app:main",
        ],
    },
)
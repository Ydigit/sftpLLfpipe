# Video to NeRF Pipeline

A GUI application that simplifies the process of converting videos to NeRF-compatible datasets.

## Features

- Extract frames from videos at customizable frame rates
- Process frames using COLMAP via the LLFF pipeline
- Upload processed datasets to a remote server for NeRF training
- User-friendly GUI interface

## Installation

### Prerequisites

- Python 3.6 or higher
- FFmpeg (for video processing)
- COLMAP (for Structure from Motion)
- LLFF toolset (for pose estimation)

### Installing LLFF

```bash
git clone https://github.com/Fyusion/LLFF
cd LLFF
pip install -e .
```

### Installing Video to NeRF

```bash
# Clone the repository
git clone https://github.com/yourusername/video-to-nerf.git
cd video-to-nerf

# Install the package
pip install -e .
```
## Install the requirements:
```bash
pip install -r R:\Nerfs\getvid\requirements.txt

```
## Usage

### Starting the GUI

```bash
# If installed via pip
video-to-nerf

# Or run directly
python -m video_to_nerf.app
```

### Workflow

1. Select a video file
2. Set the output directory
3. Choose your desired frame rate
4. Extract frames
5. Run COLMAP/LLFF processing
6. (Optional) Upload to a remote server for NeRF training

## NeRF Training

This tool prepares data for NeRF training using the [original NeRF implementation](https://github.com/bmild/nerf).

Once your data is processed and uploaded, you can train a NeRF model with:

```bash
python run_nerf.py --config config_your_dataset_name.txt
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
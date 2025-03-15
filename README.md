# Simple Media Caption

A minimalistic application for media captioning and masking using Python and Tkinter. This tool allows users to efficiently annotate images and videos with captions and create polygon-based masks for various computer vision and machine learning applications.

## Features

- Project-based workflow with save/load functionality
- Support for images and videos (mp4)
- Media preview with video playback controls
- Text captioning for media files
- Polygon-based masking tools (in progress)
- Dataset export functionality (diffusion-pipe compatible)
- Intuitive user interface built with Tkinter
- Theoretically cross-platform (I test on Windows)

## Requirements

- Python 3.6+
- Pillow
- OpenCV
- NumPy

## Installation

1. Clone this repository:
```bash
git clone https://github.com/MykytaPetrenko/simple-media-caption.git
cd simple-media-caption
```

2. Create a virtual environment:
```bash
python -m venv .venv
# On Windows
.venv/Scripts/activate
# On macOS/Linux
source .venv/bin/activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

### Workflow

1. Create a new project or open an existing one
2. Set the media path to a folder containing images and videos
3. Select media files from the list to view and edit
4. Add captions in the text box at the bottom
5. Create and edit masks using the tools in the left panel
6. Save your project regularly
7. Export as a dataset when finished

## Project Structure

- `main.py`: Application entry point and initialization
- `app/application.py`: Main application class and window management
- `app/project_manager.py`: Project loading/saving functionality
- `app/media_viewer.py`: Media display and playback controls
- `app/mask_manager.py`: Mask creation, editing, and management
- `app/ui_components.py`: UI panels and controls
- `requirements.txt`: Project dependencies

## Known Issues

It is a new tool, so I guess there are a lot of them, but I have not found them yet.

## Roadmap

- ✅ Mask Tracking (OpenCV)
- ✅ Export mask file for masked training
-  Keyboard shortcuts for common operations
-  Advanced mask manipulation tools

## License

This project is licensed under the GPL 3.0.
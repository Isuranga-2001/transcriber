# Video Transcriber

A simple yet powerful command-line tool that transcribes speech from video files into text using the Vosk speech recognition model.

## Prerequisites

1. Python 3.6 or higher
2. FFmpeg installed and added to your system PATH
3. Required Python packages:

```python
vosk
```

## Installing Vosk Model

1. Download the English model from the official Vosk website:
   - Visit [Vosk Models](https://alphacephei.com/vosk/models)
   - Download the model `vosk-model-en-us-0.22` (approximately 1.8GB)

2. Extract the downloaded model to a location on your computer

3. Update the `MODEL_PATH` in `transcribe.py`:

   ```python
   MODEL_PATH = "path/to/your/vosk-model-en-us-0.22"  # Change this to your model path
   ```

## Installation

1. Clone this repository or download the `transcribe.py` file

2. Install the required Python package:

   ```bash
   pip install vosk
   ```

3. Make sure FFmpeg is installed on your system:
   - Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)
   - Linux: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`

## Usage

Basic usage:

```bash
python transcribe.py <video_file_path>
```

Example:

```bash
python transcribe.py my_video.mp4
```

The script will:

1. Extract audio from the video file
2. Process the audio using the Vosk model
3. Generate a transcript file in the same directory as the video
4. The output file will be named `<video_name>_transcript.txt`

## Features

- Supports various video formats (thanks to FFmpeg)
- Automatically extracts and processes audio
- Progress indicator during transcription
- Outputs word count upon completion
- Cleans up temporary files automatically

## Notes

- The transcription speed depends on your CPU power and the length of the video
- Make sure you have enough disk space for the Vosk model and temporary audio files
- The model provides good accuracy for clear English speech
- Background noise might affect transcription quality

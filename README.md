# Video Transcriber

A simple yet powerful command-line tool that transcribes speech from video files or live system audio into text using the Vosk speech recognition model.

## Prerequisites

1. Python 3.6 or higher
2. FFmpeg installed and added to your system PATH
3. Required Python packages:

```python
vosk
sounddevice  # Required for live audio transcription
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
   pip install vosk sounddevice
   ```

3. Make sure FFmpeg is installed on your system:
   - Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)
   - Linux: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`

## Usage

### Transcribe a Video File

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

### Transcribe Live System Audio

Capture and transcribe audio playing on your computer in real-time (e.g., meetings, videos, podcasts).

```bash
python transcribe.py --live
```

#### List Available Audio Devices

To find the correct audio device for capturing system audio:

```bash
python transcribe.py --list-devices
```

#### Specify Audio Device

Use a specific audio device by its index:

```bash
python transcribe.py --live --device 5
```

#### Custom Output File

Save the live transcript to a custom file:

```bash
python transcribe.py --live --output meeting_notes.txt
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `video_file` | Path to video file to transcribe |
| `--live` | Transcribe live system audio (loopback) |
| `--list-devices` | List available audio devices |
| `--device <index>` | Audio device index for live transcription |
| `--output`, `-o` | Output file for live transcription (default: `live_transcript.txt`) |

### Setting Up System Audio Capture (Windows)

To capture system audio (not microphone input), you may need to:

1. **Enable Stereo Mix:**
   - Right-click the speaker icon in the system tray
   - Select "Sounds" → "Recording" tab
   - Right-click in the empty area → "Show Disabled Devices"
   - Enable "Stereo Mix" if available

2. **Use Virtual Audio Cable (Alternative):**
   - Install software like [VB-Audio Virtual Cable](https://vb-audio.com/Cable/)
   - Route system audio through the virtual cable
   - Select the virtual cable as the input device

## Features

- Supports various video formats (thanks to FFmpeg)
- Automatically extracts and processes audio
- **Live system audio transcription** (loopback recording)
- Real-time transcription with partial results display
- Auto-detection of loopback audio devices
- Progress indicator during transcription
- Outputs word count upon completion
- Cleans up temporary files automatically

## Notes

- The transcription speed depends on your CPU power and the length of the video
- Make sure you have enough disk space for the Vosk model and temporary audio files
- The model provides good accuracy for clear English speech
- Background noise might affect transcription quality
- For live transcription, press `Ctrl+C` to stop and save the transcript
- Live transcription requires a loopback-capable audio device or virtual audio cable

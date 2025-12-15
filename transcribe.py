from vosk import Model, KaldiRecognizer
import sys, json, wave, os, tempfile
import subprocess
import queue
import threading

MODEL_PATH = r"F:/Models/vosk-model-en-us-0.22"  # <-- change to your model path
SAMPLE_RATE = 16000

def extract_audio_from_video(video_path):
    """Extract audio from video and convert to WAV mono 16-bit PCM at 16 kHz"""
    if not os.path.exists(video_path):
        sys.exit(f"Video file not found: {video_path}")
    
    # Create temporary WAV file
    temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_audio_path = temp_audio.name
    temp_audio.close()
    
    try:
        # Use ffmpeg to extract audio and convert to required format
        cmd = [
            'ffmpeg', '-i', video_path,
            '-acodec', 'pcm_s16le',  # 16-bit PCM
            '-ar', '16000',          # 16 kHz sample rate
            '-ac', '1',              # mono
            '-y',                    # overwrite output file
            temp_audio_path
        ]
        
        print(f"Extracting audio from video: {video_path}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            sys.exit(f"Error extracting audio: {result.stderr}")
            
        print("Audio extraction completed successfully")
        return temp_audio_path
        
    except FileNotFoundError:
        sys.exit("ffmpeg not found. Please install ffmpeg and add it to your PATH.")

def transcribe_video(video_path):
    """Transcribe video file to text"""
    # Extract audio from video
    audio_path = extract_audio_from_video(video_path)
    
    try:
        # Use a context manager so the WAV file is always closed even if Model() raises
        with wave.open(audio_path, "rb") as wf:
            # Verify audio format (should be correct from ffmpeg conversion)
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                sys.exit("Audio format verification failed.")

            # Validate model path before attempting to load
            print("Loading speech recognition model...")
            if not os.path.isdir(MODEL_PATH) or not os.listdir(MODEL_PATH):
                sys.exit(f"Model folder '{MODEL_PATH}' does not exist or appears empty.\n"
                         "Download a Vosk model and set MODEL_PATH to the model directory.")

            try:
                model = Model(MODEL_PATH)
            except Exception as e:
                # Provide clearer guidance when model fails to load
                sys.exit(f"Failed to load Vosk model at '{MODEL_PATH}': {e}\n"
                         "Make sure the path points to a valid Vosk model directory.")

            rec = KaldiRecognizer(model, wf.getframerate())

            print("Starting transcription...")
            full_text = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    if text:
                        full_text.append(text)
                        print(".", end="", flush=True)  # Progress indicator

            # Final partial result
            final_result = json.loads(rec.FinalResult())
            final_text = final_result.get("text", "")
            if final_text:
                full_text.append(final_text)

            # Save transcript
            transcript_content = " ".join(full_text)
            output_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}_transcript.txt"

            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(transcript_content)

            print(f"\nTranscription completed!")
            print(f"Transcript saved to: {output_filename}")
            print(f"Total words transcribed: {len(transcript_content.split())}")

    finally:
        # Clean up temporary audio file (safe because 'with' closed the file)
        if os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
            except PermissionError:
                print(f"Warning: could not delete temporary audio file '{audio_path}' because it is in use.")


def list_audio_devices():
    """List all available audio devices for loopback recording"""
    try:
        import sounddevice as sd
    except ImportError:
        sys.exit("sounddevice not found. Install it with: pip install sounddevice")
    
    devices = sd.query_devices()
    
    print("\n=== Available Audio Devices ===")
    print(f"{'Index':<6} {'Name':<60} {'Type':<12} {'In':<4} {'Out':<4}")
    print("-" * 90)
    
    for i, dev in enumerate(devices):
        # Mark default devices
        marker = ""
        if i == sd.default.device[0]:
            marker = " [Default Input]"
        elif i == sd.default.device[1]:
            marker = " [Default Output]"
        
        name = dev['name'] + marker
        host_api = sd.query_hostapis(dev['hostapi'])['name']
        inputs = dev['max_input_channels']
        outputs = dev['max_output_channels']
        
        print(f"{i:<6} {name:<60} {host_api:<12} {inputs:<4} {outputs:<4}")
    
    print("\nLook for devices with 'Loopback' or 'Stereo Mix' for system audio capture.")
    print("On Windows WASAPI, loopback devices typically have 'loopback' in the name or")
    print("you can use the output device index with loopback enabled.\n")
    
    # Try to find WASAPI loopback devices
    try:
        wasapi_devices = []
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                name_lower = dev['name'].lower()
                if 'loopback' in name_lower or 'stereo mix' in name_lower or 'what u hear' in name_lower:
                    host_api = sd.query_hostapis(dev['hostapi'])['name']
                    wasapi_devices.append((i, dev['name'], host_api))
        
        if wasapi_devices:
            print("=== Recommended Loopback Devices ===")
            for idx, name, api in wasapi_devices:
                print(f"  Device {idx}: {name} ({api})")
            print("\nTip: WASAPI devices (index 18) usually provide best quality for system audio.")
    except Exception as e:
        print(f"Could not detect loopback devices: {e}")


def transcribe_live_audio(device_index=None, output_file="live_transcript.txt"):
    """Transcribe live system audio (loopback) in real-time"""
    try:
        import sounddevice as sd
    except ImportError:
        sys.exit("sounddevice not found. Install it with: pip install sounddevice")
    
    # Check device accessibility before loading the model
    try:
        test_stream = sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=8000,
            device=device_index,
            dtype='int16',
            channels=1
        )
        test_stream.close()
    except Exception as e:
        sys.exit(f"Could not access audio device {device_index}: {e}\nTry running with --list-devices to see available devices.")

    # Validate model path before attempting to load
    print("Loading speech recognition model...")
    if not os.path.isdir(MODEL_PATH) or not os.listdir(MODEL_PATH):
        sys.exit(f"Model folder '{MODEL_PATH}' does not exist or appears empty.\n"
                 "Download a Vosk model and set MODEL_PATH to the model directory.")

    try:
        model = Model(MODEL_PATH)
    except Exception as e:
        sys.exit(f"Failed to load Vosk model at '{MODEL_PATH}': {e}\n"
                 "Make sure the path points to a valid Vosk model directory.")

    rec = KaldiRecognizer(model, SAMPLE_RATE)
    rec.SetWords(True)

    audio_queue = queue.Queue()
    full_text = []
    is_running = True

    def audio_callback(indata, frames, time_info, status):
        """Callback function for audio stream"""
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        audio_queue.put(bytes(indata))
    
    # Determine device to use
    if device_index is None:
        # Try to find a suitable loopback device automatically
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                name = dev['name'].lower()
                if 'loopback' in name or 'stereo mix' in name:
                    device_index = i
                    print(f"Auto-detected loopback device: {dev['name']}")
                    break
        
        if device_index is None:
            print("\nNo loopback device auto-detected.")
            print("Tip: On Windows, you may need to:")
            print("  1. Enable 'Stereo Mix' in Sound settings, or")
            print("  2. Use a virtual audio cable software, or")
            print("  3. Run with --list-devices to see available devices")
            print("  4. Then specify device with --device <index>\n")
            
            # Fall back to default input device
            default_device = sd.default.device[0]
            if default_device is not None:
                device_index = default_device
                print(f"Falling back to default input device: {sd.query_devices(device_index)['name']}")
            else:
                sys.exit("No audio input device available.")
    
    device_info = sd.query_devices(device_index)
    print(f"\nUsing audio device: {device_info['name']}")
    
    # Get the number of channels from the device
    channels = min(device_info['max_input_channels'], 2)
    if channels == 0:
        sys.exit(f"Device {device_index} has no input channels. Select a different device.")
    
    print(f"Starting live transcription... (Press Ctrl+C to stop)")
    print("-" * 50)
    
    try:
        # Open audio stream
        with sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=8000,
            device=device_index,
            dtype='int16',
            channels=1,  # Vosk requires mono
            callback=audio_callback
        ):
            while is_running:
                try:
                    data = audio_queue.get(timeout=0.5)
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text = result.get("text", "")
                        if text:
                            full_text.append(text)
                            print(f"\r[Transcribed]: {text}")
                    else:
                        # Partial result for real-time feedback
                        partial = json.loads(rec.PartialResult())
                        partial_text = partial.get("partial", "")
                        if partial_text:
                            print(f"\r[Listening]: {partial_text}...", end="", flush=True)
                except queue.Empty:
                    continue
                    
    except KeyboardInterrupt:
        print("\n\nStopping transcription...")
    except sd.PortAudioError as e:
        sys.exit(f"Audio device error: {e}\nTry running with --list-devices to see available devices.")
    
    # Get final result
    final_result = json.loads(rec.FinalResult())
    final_text = final_result.get("text", "")
    if final_text:
        full_text.append(final_text)
    
    # Save transcript
    transcript_content = " ".join(full_text)
    if transcript_content.strip():
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(transcript_content)
        print(f"\nTranscription completed!")
        print(f"Transcript saved to: {output_file}")
        print(f"Total words transcribed: {len(transcript_content.split())}")
    else:
        print("\nNo speech detected during the session.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Transcribe video files or live system audio to text using Vosk",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Transcribe a video file:
    python transcribe.py video.mp4
    
  Transcribe live system audio:
    python transcribe.py --live
    
  List available audio devices:
    python transcribe.py --list-devices
    
  Transcribe from specific device:
    python transcribe.py --live --device 5
    
  Save live transcript to custom file:
    python transcribe.py --live --output my_transcript.txt
        """
    )
    
    parser.add_argument("video_file", nargs="?", help="Path to video file to transcribe")
    parser.add_argument("--live", action="store_true", help="Transcribe live system audio (loopback)")
    parser.add_argument("--list-devices", action="store_true", help="List available audio devices")
    parser.add_argument("--device", type=int, default=None, help="Audio device index for live transcription")
    parser.add_argument("--output", "-o", default="live_transcript.txt", help="Output file for live transcription")
    
    args = parser.parse_args()
    
    if args.list_devices:
        list_audio_devices()
    elif args.live:
        transcribe_live_audio(device_index=args.device, output_file=args.output)
    elif args.video_file:
        transcribe_video(args.video_file)
    else:
        parser.print_help()
        sys.exit(1)

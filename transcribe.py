from vosk import Model, KaldiRecognizer
import sys, json, wave, os, tempfile
import subprocess

MODEL_PATH = r"F:/Models/vosk-model-en-us-0.22"  # <-- change to your model path

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
        # Open the extracted audio file
        wf = wave.open(audio_path, "rb")
        
        # Verify audio format (should be correct from ffmpeg conversion)
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            sys.exit("Audio format verification failed.")

        # Load Vosk model
        print("Loading speech recognition model...")
        model = Model(MODEL_PATH)
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

        wf.close()
        
        # Save transcript
        transcript_content = " ".join(full_text)
        output_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}_transcript.txt"
        
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(transcript_content)

        print(f"\nTranscription completed!")
        print(f"Transcript saved to: {output_filename}")
        print(f"Total words transcribed: {len(transcript_content.split())}")
        
    finally:
        # Clean up temporary audio file
        if os.path.exists(audio_path):
            os.unlink(audio_path)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python transcribe.py <video_file_path>")
        print("Example: python transcribe.py video.mp4")
        sys.exit(1)
    
    video_file = sys.argv[1]
    transcribe_video(video_file)

# src/test_clip.py
import os
from dotenv import load_dotenv
from main import on_event
from pydub import AudioSegment

load_dotenv()  # load env vars before using senders

# -------------------------------
# CONFIG: test audio file
# Supports .mp3 or .wav
# -------------------------------
input_file = "clips/man-s.mp3"  # replace with your file
clips_folder = "clips"
os.makedirs(clips_folder, exist_ok=True)

# Convert MP3 -> WAV if needed
if input_file.lower().endswith(".mp3"):
    wav_file = os.path.join(clips_folder, os.path.splitext(os.path.basename(input_file))[0] + ".wav")
    print(f"Converting MP3 to WAV: {wav_file}")
    audio = AudioSegment.from_mp3(input_file)
    audio = audio.set_channels(1).set_frame_rate(16000)  # mono 16kHz
    audio.export(wav_file, format="wav")
    clip_path = wav_file
else:
    clip_path = input_file

if not os.path.isfile(clip_path):
    raise FileNotFoundError(f"Audio file not found: {clip_path}")

print(f"Testing with audio clip: {clip_path}\n")

# Trigger main event function
on_event(clip_path)
print("\nTest completed.")

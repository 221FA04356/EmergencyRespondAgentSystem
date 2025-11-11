# src/processor.py
from transformers import pipeline

# ASR pipeline (choose a small whisper model for speed)
asr = pipeline("automatic-speech-recognition", model="openai/whisper-tiny")  # tiny / small as per resource
# zero-shot classifier (no fine-tuning required for prototype)
zero_shot = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def transcribe(audio_path):
    print("Transcribing:", audio_path)
    out = asr(audio_path, return_timestamps=True)
    return out.get("text", "")

def classify_transcript(text):
    candidate_labels = ["threat", "safe", "uncertain"]
    out = zero_shot(text, candidate_labels)
    # returns dict: labels (ordered), scores
    return out
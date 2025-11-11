# src/processor.py
#from transformers import pipeline

# ASR pipeline (choose a small whisper model for speed)
asr = pipeline("automatic-speech-recognition", model="openai/whisper-tiny")  # tiny / small as per resource
# zero-shot classifier (no fine-tuning required for prototype)
zero_shot = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def transcribe(file_path):
    # placeholder for deployment; real transcription only works locally
    return "transcription not available on free instance"

def classify_transcript(transcript):
    # dummy classification
    return {"labels": ["safe"], "scores": [0.0]}

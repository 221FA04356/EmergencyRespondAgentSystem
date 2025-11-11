# src/processor.py
import random

# Dummy transcription function
def transcribe(file_path):
    # You can return a placeholder or fixed text
    return "Transcription not available on free deployment."

# Dummy classification function
def classify_transcript(transcript):
    # Return a dummy classification
    labels = ["safe", "threat"]
    # Randomly pick one for demo
    top_label = random.choice(labels)
    top_score = round(random.uniform(0.0, 1.0), 2)
    return {
        "labels": [top_label],
        "scores": [top_score]
    }

# src/main.py

import os
import time
from dotenv import load_dotenv
from src.recorder import AudioMonitor
from src.processor import transcribe, classify_transcript
from src.popup_alert import show_confirm_popup
from src.senders import send_sms, send_email

from datetime import datetime

# Load environment variables
load_dotenv()  # loads .env before using senders


def wait_for_file_ready(path, min_size=2048, timeout=5):
    """
    Wait until a file is fully written and ready for use.
    Prevents processing half-written clips.
    """
    start = time.time()
    while (not os.path.exists(path) or os.path.getsize(path) < min_size) and (time.time() - start) < timeout:
        time.sleep(0.2)
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    if os.path.getsize(path) < min_size:
        raise IOError(f"File too small or incomplete: {path}")
    return True


def on_event(clip_path):
    """Handles audio event callback after clip is saved."""
    print("🎧 Event clip saved:", clip_path)

    # ✅ Ensure file is ready before processing
    try:
        wait_for_file_ready(clip_path, min_size=4096, timeout=8)
        time.sleep(0.5)  # short delay to ensure disk flush
    except Exception as e:
        print("⚠ File readiness check failed:", e)
        return

    # 1️⃣ Transcribe the audio
    try:
        transcript = transcribe(clip_path)
        print("🗣 Transcript:", transcript)
    except Exception as e:
        print("⚠ Transcription failed:", e)
        return

    # 2️⃣ Classify the transcript
    try:
        cls = classify_transcript(transcript)
        print("🔍 Classification:", cls)
    except Exception as e:
        print("⚠ Classification failed:", e)
        return

    top_label = cls.get("labels", [None])[0]
    top_score = cls.get("scores", [0])[0]
    print(f"📊 Top label: {top_label}, score={top_score:.3f}")

    alert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    snippet = transcript.replace("\n", " ").strip()
    MAX_SMS_LENGTH = 160

    # 3️⃣ Handle classification results

    # CASE 1: Threat (high confidence)
    if top_label == "threat" or top_score > 0.7:
        action = show_confirm_popup(transcript, clip_path, timeout=20)
        print("🧍 User action:", action)
        if action == "safe":
            print("✅ User confirmed safe. No alert sent.")
            return
        
        sms_message = f"ALERT! Danger detected. Time: {alert_time}. Source: {clip_path}. {snippet}..."
        sms_message = sms_message[:MAX_SMS_LENGTH]
        email_subject = "URGENT: Danger detected"
        email_body = f"ALERT: Danger detected!\nTime: {alert_time}\nTranscript:\n{transcript}\nSource clip: {clip_path}"

    # CASE 2: Uncertain (medium confidence)
    elif top_label == "uncertain" or (0.4 < top_score <= 0.7):
        action = show_confirm_popup(transcript, clip_path, timeout=20)
        print("🧍 User action:", action)
        if action == "safe":
            print("✅ User confirmed safe. No alert sent.")
            return
        
        sms_message = f"WARNING! Possible concern detected. Time: {alert_time}. Source: {clip_path}. {snippet}..."
        sms_message = sms_message[:MAX_SMS_LENGTH]
        email_subject = "NOTICE: Possible concern detected"
        email_body = f"WARNING: Possible concern detected.\nTime: {alert_time}\nTranscript:\n{transcript}\nSource clip: {clip_path}"

    # CASE 3: Safe (low confidence)
    else:
        print("🟢 Classified safe. No action taken.")
        return

    # 4️⃣ Send SMS alert
    try:
        print(f"📨 SMS length: {len(sms_message)}")
        send_sms(sms_message)
        print("✅ SMS alert sent successfully!")
    except Exception as e:
        print("❌ Failed to send SMS:", e)

    # 5️⃣ Send email alert
    try:
        send_email(email_subject, email_body, attachment_path=clip_path)
        print("✅ Email alert sent successfully!")
    except Exception as e:
        print("❌ Failed to send email:", e)


if __name__ == "__main__":
    # Ensure output folder exists
    os.makedirs("clips", exist_ok=True)

    # Initialize audio monitor
    monitor = AudioMonitor(out_folder="clips")

    # Begin continuous listening loop
    print("🎤 Starting audio monitor... Waiting for events.")
    monitor.run(on_event)

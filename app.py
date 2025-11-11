# app.py
import os
import time
import queue
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from src.processor import transcribe, classify_transcript
from src.senders import send_sms, send_email

app = Flask(__name__, template_folder="templates", static_folder="static")

# storage
EVENT_QUEUE = queue.Queue()        # events produced by uploads
LATEST_EVENT = {}                  # last event (for quick display)

CLIP_FOLDER = "clips"
os.makedirs(CLIP_FOLDER, exist_ok=True)


def build_event_object(clip_path, transcript, classification):
    labels = classification.get("labels", [])
    scores = classification.get("scores", [])
    top_label = labels[0] if labels else None
    top_score = scores[0] if scores else 0.0
    event = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "clip_path": clip_path,
        "transcript": transcript,
        "classification": classification,
        "top_label": top_label,
        "top_score": top_score
    }
    return event


# ---------------- Routes ----------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    """Upload an audio file for immediate analysis. Returns result and a trigger flag if popup should appear."""
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "no file"}), 400

    filename = f.filename
    safe_name = f"upload_{int(time.time())}_{filename}"
    save_path = os.path.join(CLIP_FOLDER, safe_name)
    f.save(save_path)

    try:
        transcript = transcribe(save_path)
    except Exception as e:
        return jsonify({"error": f"transcription failed: {e}"}), 500

    try:
        cls = classify_transcript(transcript)
    except Exception as e:
        cls = {"labels": ["unknown"], "scores": [0.0], "error": str(e)}

    labels = cls.get("labels", [])
    scores = cls.get("scores", [])
    top_label = labels[0] if labels else "unknown"
    top_score = scores[0] if scores else 0.0

    event = build_event_object(save_path, transcript, cls)
    # return event and indicate popup if threat/uncertain by your thresholds
    trigger_popup = (top_label == "threat") or (0.4 < top_score)
    return jsonify({"event": event, "trigger": trigger_popup})


@app.route("/start_live", methods=["POST"])
def start_live():
    """Live monitoring disabled in Render free instance."""
    return jsonify({"status": "disabled"})


@app.route("/stop_live", methods=["POST"])
def stop_live():
    """Live monitoring disabled in Render free instance."""
    return jsonify({"status": "disabled"})


@app.route("/poll_events", methods=["GET"])
def poll_events():
    """Frontend polls this endpoint to receive events queued by uploads."""
    events = []
    while not EVENT_QUEUE.empty():
        events.append(EVENT_QUEUE.get())
    latest = LATEST_EVENT.copy()
    return jsonify({"events": events, "latest": latest})


@app.route("/send_alert", methods=["POST"])
def send_alert():
    """
    Called by frontend when user didn't respond within timeout or clicked Send Alert.
    Expects JSON: { "transcript": "...", "clip_path": "..." }
    Sends SMS and Email using your existing senders.
    """
    data = request.get_json() or {}
    transcript = data.get("transcript", "")
    clip_path = data.get("clip_path")

    alert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    snippet = (transcript or "").replace("\n", " ").strip()
    MAX_SMS = 160
    sms_message = f"ALERT! Danger detected. Time: {alert_time}. {snippet[:MAX_SMS]}"
    sms_message = sms_message[:MAX_SMS]
    email_subject = "URGENT: Danger detected"
    email_body = f"ALERT: Danger detected!\nTime: {alert_time}\nTranscript:\n{transcript}\nSource: {clip_path or 'N/A'}"

    sms_sent = False
    email_sent = False
    sms_err = None
    email_err = None

    try:
        send_sms(sms_message)
        sms_sent = True
    except Exception as e:
        sms_err = str(e)
    try:
        send_email(email_subject, email_body, attachment_path=clip_path)
        email_sent = True
    except Exception as e:
        email_err = str(e)

    return jsonify({"sms_sent": sms_sent, "email_sent": email_sent, "sms_err": sms_err, "email_err": email_err})


@app.route("/user_response", methods=["POST"])
def user_response():
    """Called when user presses "I'm Safe" in web UI. No alert is sent."""
    data = request.get_json() or {}
    return jsonify({"status": "user_safe"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

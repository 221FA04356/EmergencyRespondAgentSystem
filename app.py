# app.py
import os
import time
import threading
import queue
from datetime import datetime
from flask import Flask, render_template, request, jsonify

# Import your modules from src (do NOT import src.main to avoid changing CLI behavior)
# from src.recorder import AudioMonitor
from src.processor import transcribe, classify_transcript
from src.senders import send_sms, send_email

app = Flask(__name__, template_folder="templates", static_folder="static")

# storage
EVENT_QUEUE = queue.Queue()        # events produced by live monitor
LATEST_EVENT = {}                  # last event (for quick display)
MONITOR_THREAD = None
MONITOR_THREAD_LOCK = threading.Lock()
MONITOR_RUNNING = False

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


def monitor_callback(clip_path):
    """This callback is called by AudioMonitor when it saves a clip."""
    try:
        transcript = transcribe(clip_path)
    except Exception as e:
        transcript = f"[transcription error: {e}]"

    try:
        cls = classify_transcript(transcript)
    except Exception as e:
        cls = {"labels": ["unknown"], "scores": [0.0], "error": str(e)}

    event = build_event_object(clip_path, transcript, cls)

    # push into queue for frontend polling
    EVENT_QUEUE.put(event)
    LATEST_EVENT.clear()
    LATEST_EVENT.update(event)

    # (Important) do NOT auto-send alerts here — web UI will show modal and call /send_alert if needed
    print(f"[monitor_callback] Event queued: {event['top_label']} {event['top_score']:.3f}")


def start_monitor_thread():
    global MONITOR_THREAD, MONITOR_RUNNING
    with MONITOR_THREAD_LOCK:
        if MONITOR_THREAD and MONITOR_THREAD.is_alive():
            return False
        MONITOR_RUNNING = True

        def _thread_target():
            monitor = AudioMonitor(out_folder=CLIP_FOLDER)
            try:
                monitor.run(monitor_callback)  # blocking until KeyboardInterrupt — but we run in separate daemon thread
            except Exception as e:
                print("[monitor thread] Exception:", e)
            finally:
                print("[monitor thread] Exited")

        MONITOR_THREAD = threading.Thread(target=_thread_target, daemon=True)
        MONITOR_THREAD.start()
        return True


def stop_monitor_thread():
    global MONITOR_RUNNING
    # AudioMonitor.run currently exits on KeyboardInterrupt only. We rely on user to stop process or add a stop mechanism.
    # But for this implementation we provide a flag to indicate requested stop; actual stopping may require changes in recorder.
    MONITOR_RUNNING = False
    return True


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
    started = start_monitor_thread()
    if started:
        return jsonify({"status": "started"})
    else:
        return jsonify({"status": "already_running"})


@app.route("/stop_live", methods=["POST"])
def stop_live():
    # stopping the AudioMonitor gracefully would require a stop API in recorder; here we return a flag
    stopped = stop_monitor_thread()
    return jsonify({"status": "stopped" if stopped else "failed"})


@app.route("/poll_events", methods=["GET"])
def poll_events():
    """
    Frontend polls this endpoint frequently (1s) to receive events queued by monitor_callback.
    Returns list of events (could be 0 or more). We drain the queue.
    """
    events = []
    while not EVENT_QUEUE.empty():
        events.append(EVENT_QUEUE.get())
    # also include latest summary
    latest = LATEST_EVENT.copy()
    return jsonify({"events": events, "latest": latest})


@app.route("/send_alert", methods=["POST"])
def send_alert():
    """
    Called by frontend when user didn't respond within timeout or user clicked Send Alert.
    Expects JSON: { "transcript": "...", "clip_path": "..." (optional) }
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
    """
    Called when user presses "I'm Safe" in web UI. No alert is sent.
    """
    data = request.get_json() or {}
    # log or store response if needed
    return jsonify({"status": "user_safe"})


if __name__ == "__main__":

    app.run(debug=True, port=5000)

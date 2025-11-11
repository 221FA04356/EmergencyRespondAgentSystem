# src/popup_and_alert.py
import tkinter as tk
import threading
import time
import simpleaudio as sa
import os

def _play_audio_nonblocking(path):
    try:
        wave_obj = sa.WaveObject.from_wave_file(path)
        play_obj = wave_obj.play()
        return play_obj
    except Exception as e:
        print("Audio playback failed:", e)
        return None

def show_confirm_popup(transcript, audio_path, timeout=20):
    """
    Shows a modal popup with transcript + play button + 2 choices:
    Returns 'safe' if user confirms safe, 'alert' if user chooses alert, or 'timeout' on timeout.
    """
    result = {"action": None}
    root = tk.Tk()
    root.title("Safety Confirmation")
    root.geometry("450x220")
    tk.Label(root, text="We detected a potential dangerous sound. Transcript:", wraplength=420).pack(pady=(10,0))
    tk.Message(root, text=transcript, width=420).pack()
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    def on_safe():
        result["action"] = "safe"
        root.destroy()

    def on_alert():
        result["action"] = "alert"
        root.destroy()

    tk.Button(btn_frame, text="I'm Safe", width=16, command=on_safe).pack(side='left', padx=8)
    tk.Button(btn_frame, text="Send Alert", width=16, command=on_alert).pack(side='right', padx=8)

    # play audio
    _play_audio_nonblocking(audio_path)

    # timeout handler
    def timer():
        time.sleep(timeout)
        if result["action"] is None:
            result["action"] = "timeout"
            try:
                root.after(0, root.destroy)
            except:
                pass

    threading.Thread(target=timer, daemon=True).start()
    root.mainloop()
    return result["action"]

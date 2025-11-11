// static/script.js
let pollInterval = null;
let modalTimer = null;
let countdown = 0;
let currentEvent = null;

// Upload handler
document.addEventListener('DOMContentLoaded', () => {
  const uploadForm = document.getElementById('uploadForm');
  uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('uploadFile');
    if (!fileInput.files.length) return alert('Choose a file first');
    const fd = new FormData();
    fd.append('file', fileInput.files[0]);
    const res = await fetch('/upload', { method: 'POST', body: fd });
    const json = await res.json();
    document.getElementById('uploadResult').innerText = JSON.stringify(json.event, null, 2);
    if (json.trigger) {
      // show modal immediately for upload-triggered events
      showModal(json.event);
    }
  });

  // Live controls
  document.getElementById('startLive').addEventListener('click', async () => {
    const res = await fetch('/start_live', { method: 'POST' });
    const j = await res.json();
    document.getElementById('liveStatus').innerText = `Status: ${j.status}`;
    startPolling();
  });

  document.getElementById('stopLive').addEventListener('click', async () => {
    const res = await fetch('/stop_live', { method: 'POST' });
    const j = await res.json();
    document.getElementById('liveStatus').innerText = `Status: ${j.status}`;
    stopPolling();
  });

  document.getElementById('safeBtn').addEventListener('click', async () => {
    // user is safe
    clearModalTimer();
    await fetch('/user_response', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ response: 'safe' }) });
    hideModal();
    appendLiveResult('✅ User confirmed safe. No alert sent.');
  });

  document.getElementById('sendBtn').addEventListener('click', async () => {
    clearModalTimer();
    if (!currentEvent) return;
    const res = await fetch('/send_alert', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ transcript: currentEvent.transcript, clip_path: currentEvent.clip_path }) });
    const j = await res.json();
    hideModal();
    appendLiveResult(`🚨 Alert sent (sms: ${j.sms_sent}, email: ${j.email_sent})`);
  });
});

// Polling
function startPolling() {
  if (pollInterval) return;
  pollInterval = setInterval(async () => {
    const res = await fetch('/poll_events');
    const json = await res.json();
    if (json.events && json.events.length) {
      json.events.forEach(ev => {
        // if event is significant (threat or score > 0.4) show modal
        const top = ev.top_label;
        const score = ev.top_score || 0;
        appendLiveResult(`[${ev.timestamp}] ${top} (${score.toFixed(3)})\n${ev.transcript}\n`);
        if (top === 'threat' || score > 0.4) {
          showModal(ev);
        }
      });
    } else if (json.latest && Object.keys(json.latest).length) {
      // optional: show latest summary somewhere
    }
  }, 1200);
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
}

function appendLiveResult(text) {
  const el = document.getElementById('liveResult');
  el.innerText = `${text}\n\n${el.innerText}`;
}

// Modal functions
function showModal(event) {
  currentEvent = event;
  const modal = document.getElementById('modal');
  document.getElementById('modalTranscript').innerText = event.transcript || '(no transcript)';
  document.getElementById('modalTimer').innerText = '10';
  modal.classList.remove('hidden');

  countdown = 10;
  modalTimer = setInterval(async () => {
    countdown -= 1;
    document.getElementById('modalTimer').innerText = countdown.toString();
    if (countdown <= 0) {
      clearModalTimer();
      // auto-send alert
      const res = await fetch('/send_alert', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ transcript: currentEvent.transcript, clip_path: currentEvent.clip_path }) });
      const j = await res.json();
      hideModal();
      appendLiveResult(`⏰ Auto alert sent (sms: ${j.sms_sent}, email: ${j.email_sent})`);
    }
  }, 1000);
}

function clearModalTimer() {
  if (modalTimer) {
    clearInterval(modalTimer);
    modalTimer = null;
    countdown = 0;
  }
}

function hideModal() {
  clearModalTimer();
  currentEvent = null;
  const modal = document.getElementById('modal');
  modal.classList.add('hidden');
}
# EmergencyRespondAgentSystem

**Prerequisites (install once on the target machine)**

1. Install Python 3.11 (the project was created with 3.11).

2. Windows: download from python.org and check “Add Python to PATH”.

   Ubuntu/Debian: sudo apt install python3.11 python3.11-venv python3.11-dev (or use deadsnakes repo if needed).

3. Install Visual Studio Code and open the workspace.

4. Install the Python extension in VS Code (Marketplace: “Python” by Microsoft).

If on Windows and pip fails building a package, install the Build Tools for Visual Studio (C++ build tools).

# Twilio
#Note : Use Your own credentials. Create an account in twilio and then give your own credentials to get notifications and email to your mobile. Generate a US Trial Phone number. Also Add the phone numbers where you want to get message to in the phone numbers-> manage-> verified caller ids and add your mobile number there. 
Make sure to do this step before running the application. The credentials mentioned are not real.
#Also create a Gmail App password from Gmail account. 16 letters password.
steps 

1) Open VS Code to the project folder. Confirm the project root contains:
requirements.txt
.env
src/
clips/

2) Create and activate a fresh virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1   # if execution policy blocks, run: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
After activation, your prompt will show (.venv).

3) Select the interpreter in VS Code

Command Palette (Ctrl/Cmd+Shift+P) → Python: Select Interpreter → pick the interpreter inside the project .venv (it will show a path to .venv).
This ensures debugging, linting and Run in VS Code use the right Python.

4) Install Python package requirements

With .venv active, run:

pip install --upgrade pip
pip install -r requirements.txt

Install Microsoft c++ builder tools

Step 1. Install prebuilt C++ build tools (takes ~5–10 min)

Visit this official page:
👉 https://visualstudio.microsoft.com/visual-cpp-build-tools/

Download Build Tools for Visual Studio.

Run the installer and choose:

Desktop development with C++

(Under “Individual components”, ensure MSVC v14.x and Windows 10 SDK are selected)

Click Install and let it finish.

When done, close and reopen VS Code and your terminal.

Step 2. Try installing again

Activate your virtualenv again:

.venv\Scripts\Activate.ps1


Then reinstall the requirements:

pip install -r requirements.txt


That should now build simpleaudio successfully 🎉


Also you further need to install ffmpeg to your system and modify system variables

🧩 Step 1: Download FFmpeg

Open this official link:
🔗 https://www.gyan.dev/ffmpeg/builds/

Scroll to "Release builds"
Click ffmpeg-release-essentials.zip to download.

Once it downloads, right-click → Extract All…
Extract it to this location:

C:\ffmpeg


✅ After extraction, confirm this file exists:

C:\ffmpeg\ffmpeg-2025-xx-essentials_build\bin\ffmpeg.exe

🧭 Step 2: Add FFmpeg to System PATH

Press Windows key → type “Edit system environment variables” → Enter
It opens a window called System Properties.

Click the “Environment Variables…” button at the bottom.

In the System variables section:

Find the variable named Path

Select it → click Edit

In the edit window:

Click New

Paste the path to your FFmpeg bin folder, for example:

C:\ffmpeg\ffmpeg-2025-xx-essentials_build\bin


Click OK on all windows.

🔄 Step 3: Restart VS Code

Close all VS Code windows.

Open VS Code again.

Open a terminal (Ctrl + `).

Type:

ffmpeg -version


✅ If installed correctly, you’ll now see:

ffmpeg version 7.x.x ...

5) Run the app

From project root, with .venv active:

python -m src.main or python src/main.py

You should see console output from the app. main.py sets up an AudioMonitor and invokes monitor.run(on_event) — it watches/records audio clips into clips/ and then runs the on_event handling which may call Twilio/email.

6) Test safely (without sending messages)

To test the audio processing locally without sending SMS/email, run the included test_clip.py or temporarily comment out send_sms / send_email calls in src/main.py and replace with print(...) to confirm classification and transcription flow:

python -m src.test_clip or python src/test_clip.py

Open clips/ to verify generated wav files.



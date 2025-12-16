# Website-v3 with AI Integration

## Prerequisites
- Node.js (16+), npm
- Python 3.10+ and pip
- Optional: Create a virtual environment for the backend (recommended)

## Quick start

### Backend (Flask)
1. Create and activate a virtual environment (recommended):
   - Windows: `python -m venv .venv` then `\.venv\Scripts\activate`
   - macOS / Linux: `python -m venv .venv` then `source .venv/bin/activate`

2. Install Python dependencies and start the server:
```bash
pip install -r server/requirements.txt
python server/server.py
```
The backend will run at: **http://localhost:5002** (port is configured in `server.py`)

### Frontend (React)
Open a new terminal and run:
```bash
cd website
npm install
npm run dev
```
The frontend URL will be shown in the terminal (commonly `http://localhost:5173`).

> Tip: If you already ran `npm install` before, you can skip it on subsequent runs; use `npm run dev` to start the dev server.

---

## Features

### Voice Conversation
- Click **Start Talking** to begin; the AI asks questions and generates speech (ElevenLabs TTS).
- Your replies are captured via automatic speech recognition (ASR).
- The conversation continues automatically until the profile is complete.

### Live Message Feed
- The left sidebar shows conversation messages in an SMS-like format.
- Messages update in real-time: user messages on the right, AI messages on the left.

### Automatic Flow
1. AI speaks a question
2. App automatically starts listening
3. You speak your answer
4. AI processes it and asks the next question

---

## Backend overview
- `server/server.py` — Flask app (default port: 5002)
- Endpoints:
  - `POST /api/get_question` — Get next AI question and messages
  - `POST /api/text_to_speech` — Convert text to speech
  - `POST /api/reset` — Reset conversation
  - `GET /api/messages` — Get all messages

---

## Usage
1. Start the backend and frontend (see Quick start).
2. Open the frontend URL in your browser.
3. Click **Start Talking** and interact with the AI.
4. Click **Stop Talking** to end and reset the session.

---

## Troubleshooting
- If a port is already in use, change the port in `server/server.py` or `website` dev server config.
- To remove unused packages in the frontend, run `npm prune` inside `website`.

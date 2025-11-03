# ⚽ A2A Sports Library Agent

An **Agent-to-Agent (A2A)** microservice that handles structured football data requests, powered by **FastAPI** and **Gemini AI**.

---

## 🔍 Overview

This project receives A2A messages (via `/a2a/receive`), validates the payload, fetches league information, and uses **Gemini 2.5 Pro** to generate concise insights about winners, finals, and match results.

Once the response is ready, it sends a structured reply back to the requesting agent via a callback URL.

---

## ⚙️ Features

- **FastAPI backend** with Pydantic data models  
- **Gemini AI integration** for natural-language insights  
- **A2A protocol support** (`a2a.v1`)  
- **Callback system** for asynchronous replies  
- Built-in retry logic for AI overload errors (503 handling)

---

## 🧩 Example Flow

1. **Telex** sends a POST request:
2. **Sports Library Agent processes the message** → fetches league data → generates AI insights.
3. **Sports Library agent sends reply back to Telex**

---

🛠️ Installation
git clone https://github.com/yourusername/a2a-league-agent.git
cd a2a-league-agent
pip install -r requirements.txt


Start the app locally:

uvicorn app:web --host 0.0.0.0 --port 8000

🌐 Deployment

Deployment can be done platforms such as Render, Railway, or Docker

---

🧠 Tech Stack
1. [ ] FastAPI
2. [ ] 
3. [ ] Pydantic
4. [ ] 
5. [ ] Gemini AI API
6. [ ] 
7. [ ] Async I/O with asyncio
8. [ ] 
9. [ ] A2A Protocol (v1)

---

📜 License
MIT License © 2025
import os
import requests
import asyncio
import httpx
from datetime import datetime, UTC, timezone
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Request
from models import UserInput, A2AMessage, A2APayload
from google import genai

load_dotenv()
football_key = os.getenv('RAPID_API_KEY')
FOOTBALL_API = os.getenv("FOOTBALL_API")
ai_client = genai.Client(api_key=os.getenv("MY_API"))
WEB_URL = os.getenv("API_URL")

web = FastAPI(title="Sports Library",
              description="Produce facts about winners of top European leagues",
              version="1.0.0")


@web.post("/")
def league(country: str) -> list[str] | str:
    countries = {
        "germany": "bundesliga",
        "netherlands": "eredivisie",
        "spain": "primera division",
        "france": "ligue 1",
        "portugal": "primeira liga",
        "italy": "serie a",
        "england": "premier league"
    }

    if country.lower() not in countries:
        raise ValueError(f"❌ '{country}' is not a supported country.")

    target_league = countries[country.lower()]
    header = {"X-Auth-Token": FOOTBALL_API}

    try:
        response = requests.get(url=WEB_URL, headers=header)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"🚨 API request failed: {e}"

    web_data = response.json()
    competitions = web_data.get("competitions", [])
    store = []

    for comp in competitions:
        comp_name = comp['name']
        if target_league.lower() in comp_name.lower():
            country_name = comp["area"]["name"]
            comp_type = comp['type']

            store.append(
                f"The {comp_name} is {country_name}'s top professional {comp_type.lower()}."
            )

    # ✅ Check after loop
    if not store:
        print("No matches found. These were available:")
        avail = ([c['name'] for c in competitions])
        return f"⚠️ No competitions found for '{target_league}' These are available competitions {avail}."

    return store


# Adapter to allow reuse between A2A and REST calls
def league_adapter(country: str, year: int):
    try:
        result = league(country)
        if not result:
            raise ValueError("League returned no result")
        return result
    except Exception as e:
        return f"❌ League lookup failed: {e}"


# # -------------------- SEND DATA TO AI
async def genai_call(store: list, country: str, year: int) -> str:
    # Create a UserInput-like prompt
    contents = [
        f"{store}",
        f"Who won it in {year}?",
        f"Where was the winner's final game of the season played?",
        f"It was played against who, what was the result?",
        "Instruction: Give straight answers, use simple and formal tone."
    ]

    for attempt in range(3):

        try:
            ai_response = await asyncio.to_thread(
                ai_client.models.generate_content,
                model="gemini-2.5-pro",
                contents=contents
            )

            return ai_response.text if hasattr(ai_response, "text") else str(ai_response)
        except Exception as e:
            if "503" in str(e) and attempt < 2:
                print(f"⚠️ Gemini overloaded, retrying in 2s... (attempt {attempt + 1})")
                await asyncio.sleep(2)
            else:
                return f"❌ AI request failed: {e}"
    return "❌ AI request failed after 3 attempts."


# --- Outgoing webhook sender (runs in background) ---
async def send_reply(callback_url: str, reply: dict):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(callback_url, json=reply)
            print(f"✅ Sent reply to {callback_url}")
        except Exception as e:
            print(f"🚨 Failed to send reply: {e}")


@web.post("/a2a/receive")
async def a2a_receive(request: Request, background_tasks: BackgroundTasks):

    # Read request body
    body = await request.body()

    # Parse A2A message into a structured object
    try:
        msg = A2AMessage.model_validate_json(body)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid message format: {e}")

    # Identify message type
    ptype = msg.payload.type.lower()

    # Handle "league.query" messages
    if ptype == "league.query":
        country = msg.payload.content.get("country")
        year = msg.payload.content.get("year", datetime.now(timezone.utc).year)

        if not country:
            raise HTTPException(status_code=400, detail="Missing country in payload.content")

        # Run your main league() logic in a thread (so FastAPI stays async)
        loop = asyncio.get_event_loop()

        # an adapter that allow both /prompts and A2A reuse the same league() function
        results = await loop.run_in_executor(None, league_adapter, country, year)

        if isinstance(results, str):
            results = [results]
        genai_response = await genai_call(results, country, year)

        # Compose a reply message
        reply = {
            "meta": {
                "message_id": f"reply-{msg.meta.message_id}",
                "sent_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                "sender": "my-agent",
                "recipient": msg.meta.sender,
                "protocol": "a2a.v1",
            },
            "payload": {
                "type": "league.reply",
                "content": {
                    "result_lines": results,  # the raw data from Football API
                    "narrative": genai_response,  # Gemini’s AI summary
                },
            },
        }

        callback_url = msg.callback_url or "http://127.0.0.1:8001//dev-callback"
        background_tasks.add_task(send_reply, callback_url, reply)
        return {"status": "accepted", "message_id": msg.meta.message_id}

    # Unsupported message types
    raise HTTPException(status_code=400, detail=f"Unsupported payload.type: {msg.payload.type}")


#  local testing
@web.post("/dev-callback")
async def dev_callback(data: dict):
    print("💬 Received callback:", data)
    return {"status": "ok"}


# Health check
@web.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:web", host="127.0.0.1", port=8001, reload=True)


import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from models import UserInput
from google import genai

load_dotenv()
football_key = os.getenv('RAPID_API_KEY')
football_api = os.getenv("FOOTBALL_API")
client = genai.Client(api_key=os.getenv("MY_API"))

web = FastAPI()


@web.post("/")
def league(user: UserInput):
    countries = {
        "germany": "bundesliga",
        "netherlands": "eredivisie",
        "spain": "primera division",
        "france": "ligue 1",
        "portugal": "primeira liga",
        "italy": "serie a",
        "england": "premier league"
    }

    if user.country.lower() not in countries:
        raise ValueError(f"❌ '{user.country}' is not a supported country.")

    target_league = countries[user.country.lower()]
    web_url = "https://api.football-data.org/v4/competitions/"
    header = {"X-Auth-Token": football_api}

    try:
        response = requests.get(url=web_url, headers=header)
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

    # # ---------------------SEND DATA TO AI
    ai_response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[f"{store}"
                  f"Who won it in {user.year}"
                  "Where was the winner's final game of the season played?"
                  "It was played against who, what was the result?"
                  "Instruction: Give straight answers, use simple and formal tone"])

    record = {
        "result": store,
        "response": ai_response.text if hasattr(ai_response, "text") else str(ai_response),
    }

    return record


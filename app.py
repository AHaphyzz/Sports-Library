from fastapi import FastAPI
from models import UserInput
from dotenv import load_dotenv
from google import genai
import os
import requests

load_dotenv()

client = genai.Client(api_key=os.getenv("MY_API"))
football_key = os.getenv('RAPID_API_KEY')
football_api = os.getenv("FOOTBALL_API")

web = FastAPI()


# ---------------------GET DATA FROM API
def league(find_count):
    countries = {"germany": "bundesliga",
                 "netherlands": "eredivise",
                 "spain": "primera division",
                 "france": "ligue 1",
                 "portugal": "primeira liga",
                 "italy": "serie a",
                 "england": "premier league"}
    if find_count.lower() not in countries:
        raise ValueError(
            f"❌ '{find_count}' is not a supported country."
        )
    target_league = countries[find_count.lower()]

    web_url = "https://api.football-data.org/v4/competitions/"

    header = {"X-Auth-Token": football_api}

    response = requests.get(url=web_url, headers=header)
    response.raise_for_status()

    data = response.json()

    store = []
    competitions = data.get("competitions", [])

    for comp in competitions:
        comp_name = comp['name']
        if target_league.lower() in comp_name.lower():
            country_name = comp["area"]["name"]
            comp_type = comp['type']

            store.append(f"The {comp_name} is {country_name}'s top professional {comp_type.lower()}")
    if not store:
        print("No matches found. These were available:")
        print([c['name'] for c in competitions])  # 👈 list of all competitions
        return f"⚠️ No competitions found for '{target_league}'."

    return store


# ---------------------SEND DATA TO AI
@web.post("/prompts")
def user_prompts(user: UserInput):
    data = league(user.country)

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[f"{data}"
                  f"Who won it in {user.year}"
                  "The winner played the final game of the season against who, what is the result?"
                  "Instruction: Give straight answers, use simple and formal tone"]
    )

    record = {
        "response": response.text if hasattr(response, "text") else str(response),
    }

    return record

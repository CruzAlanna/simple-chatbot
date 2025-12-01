from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
import uuid

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI
llm = OpenAI()

# Stores: { scenario_id: { history: [...], round: 1–5 } }
scenarios = {}

class ChatMessage(BaseModel):
    message: str
    scenario_id: str


# ROOT
@app.get("/")
def index():
    return {
        "message": "Survival API is running",
        "endpoints": {
            "POST /play": "Send game messages",
            "GET /scenarios/{scenario_id}": "View game history"
        }
    }


# GAME LOGIC
@app.post("/play")
def create(chat_message: ChatMessage):
    scenario_id = chat_message.scenario_id
    user_message = chat_message.message

    # If "start" → create a new scenario
    if user_message == "start" or scenario_id not in scenarios:
        scenario_id = "scenario-" + str(uuid.uuid4())[:8]
        scenarios[scenario_id] = {
            "round": 1,
            "history": [
                {
                    "role": "developer",
                    "content": (
                        "You are an AI game engine. You give the user dramatic "
                        "end-of-the-world scenarios (Sci-fi- Example: zombies, aliens, disasters, etc.). "
                        "Each scenario has 5 rounds. After round 5, determine if "
                        "the user survives (30% chance) or dies, giving a concluding message. Ensure that there is only one round per response."
                        "The concluding message must clearly include:\n"
                        "- SURVIVED or DIED\n"
                        "- A one-word survivor type\n"
                        "Then prompt user to play again or exit."
                    )
                }
            ]
        }

    # Pull scenario state
    state = scenarios[scenario_id]
    round_num = state["round"]

    # Add user input
    state["history"].append({
        "role": "user",
        "content": user_message
    })

    # Ask OpenAI for answer
    response = llm.responses.create(
        model="gpt-4o-mini",
        temperature=1,
        input=state["history"]
    )
    assistant_message = response.output_text

    # Add assistant response
    state["history"].append({
        "role": "assistant",
        "content": assistant_message
    })

    # Check if round 5 is done
    game_over = False
    new_scenario_id = None

    if round_num > 5:
        game_over = True
        # Create a new scenario ID for when user clicks "Play Again"
        new_scenario_id = "scenario-" + str(uuid.uuid4())[:8]

    # Increment round until max
    if not game_over:
        state["round"] += 1

    return {
        "message": assistant_message,
        "scenario_id": scenario_id,
        "round": round_num,
        "game_over": game_over,
        "next_scenario_id": new_scenario_id
    }


# HISTORY
@app.get("/scenarios/{scenario_id}")
def show(scenario_id: str):
    if scenario_id not in scenarios:
        return {"error": "Scenario not found"}, 404
    return scenarios[scenario_id]


# DELETE SCENARIO
@app.delete("/scenarios/{scenario_id}")
def destroy(scenario_id: str):
    if scenario_id in scenarios:
        del scenarios[scenario_id]
        return {"message": "Scenario deleted"}
    return {"error": "Scenario not found"}, 404

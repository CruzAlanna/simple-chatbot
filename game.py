from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Configure CORS (so your React frontend can talk to this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
llm = OpenAI()

# Store scenario histories - one per user!
scenarios = {}

# Define request body structure (like Rails strong params)
class ChatMessage(BaseModel):
    message: str
    scenario_id: str = "default"

# Root endpoint
@app.get("/")
def index():
    return {
        "message": "Survival",
        "endpoints": {
            "POST /play": "Would you survival the end of the world?",
            "GET /scenarios/{scenario_id}": "Get scenario history",
            "DELETE /scenarios/{scenario_id}": "Clear scenario history"
        }
    }

# Game endpoint
@app.post("/play")
def create(chat_message: ChatMessage):
    scenario_id = chat_message.scenario_id
    user_message = chat_message.message
    
    # Initialize scenario history if it doesn't exist
    if scenario_id not in scenarios:
        scenarios[scenario_id] = [
            {"role": "developer", "content": "You are an AI assistant who gives scenario options to the user for them to choose from. The situations you give are dramatic, movie-like, end-of-the-world situation. Some examples are zombie apocalapse, alien abduction, earth spinning out of orbit, etc. Based on the user-input of the given options, you determine the next set of options. After five rounds determine if the user would survive the situation given or DIE, giving them a success or fail message. This concluding message should include a one word adjective of what kind of survivor the user is based on their answers. The concluding message should first state whether they survived or not, then follow up with the description. Send your message in a clear structured way that is easy for the user to read. You give the user a game-like experience: the user starts the game, you give one scenario with the first round of options, the user chooses, the rounds continue following the same scenario, after input from round five is given, you tell the user if they suvived or died (ensure that the user has a 20 percent chance of survival for each scenario)."}
        ]
    
    # Add user message to history
    scenarios[scenario_id].append({"role": "user", "content": user_message})
    
    # Get response from OpenAI
    response = llm.responses.create(
        model="gpt-4o-mini",
        temperature=1,
        input=scenarios[scenario_id]
    )
    
    assistant_message = response.output_text
    
    # Add assistant message to history
    scenarios[scenario_id].append({"role": "assistant", "content": assistant_message})
    
    return {
        "message": assistant_message,
        "scenario_id": scenario_id
    }

# Get scenario history
@app.get("/scenarios/{scenario_id}")
def show(scenario_id: str):
    if scenario_id not in scenarios:
        return {"error": "Scenario not found"}, 404
    
    return {
        "scenario_id": scenario_id,
        "history": scenarios[scenario_id]
    }

# Clear scenario history
@app.delete("/scenarios/{scenario_id}")
def destroy(scenario_id: str):
    if scenario_id in scenarios:
        del scenarios[scenario_id]
        return {"message": "Scenario deleted"}
    
    return {"error": "Scenario not found"}, 404
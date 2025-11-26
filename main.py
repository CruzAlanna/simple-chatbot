from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Initialize OpenAI client
llm = OpenAI()

# Store conversation history (just like in bot_00.py)
history = [
    {"role": "developer", "content": "You are an AI assistant whose name is Robert'."}
]

# Define request body structure (like Rails strong params)
class ChatMessage(BaseModel):
    message: str

# Root endpoint
@app.get("/")
def index():
    return {"message": "Robert Chatbot API is running!"}

# Chat endpoint
@app.post("/chat")
def create(chat_message: ChatMessage):
    # Add user message to history
    history.append({"role": "user", "content": chat_message.message})
    
    # Get response from OpenAI (same as bot_00.py!)
    response = llm.responses.create(
        model="gpt-4o-mini",
        temperature=1,
        input=history
    )
    
    assistant_message = response.output_text
    
    # Add assistant message to history
    history.append({"role": "assistant", "content": assistant_message})
    
    return {"message": assistant_message}
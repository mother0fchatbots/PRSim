from fastapi import FastAPI, HTTPException # Make sure HTTPException is imported
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uuid
import json
from typing import Dict, List # Import List here
import asyncio # Import asyncio if not already present
from fastapi.middleware.cors import CORSMiddleware

# Assuming gemini_chat_service.py is in the same directory
import gemini_chat_service # The chat logic, including GeminiChatSession

# Define the path to your frontend directory (adjust "Frontend" if your folder is "frontend")
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "Frontend")

app = FastAPI()

#configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Mount the static files directory
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# In-memory store for chat sessions
chat_sessions: Dict[str, gemini_chat_service.GeminiChatSession] = {}

# Load scenarios from scenarios.json at startup
scenarios_data = {}
scenarios_file_path = os.path.join(FRONTEND_DIR, "scenarios.json")
if os.path.exists(scenarios_file_path):
    with open(scenarios_file_path, 'r', encoding='utf-8') as f:
        scenarios_list = json.load(f)
        for s in scenarios_list:
            scenarios_data[s['id']] = s # Store by string ID
    print(f"DEBUG_BACKEND: Loaded {len(scenarios_data)} scenarios from {scenarios_file_path}")
else:
    print(f"ERROR_BACKEND: scenarios.json not found at {scenarios_file_path}")
    # Handle this more gracefully in a production app, perhaps by exiting or serving a default
    scenarios_data = {} # Ensure it's empty if file not found


# Pydantic model for the chat request body
class ChatRequest(BaseModel):
    message: str
    session_id: str # Include session_id in the request
    scenario_id: str # Include scenario_id in the request

# Pydantic model for the chat response body
class ChatResponse(BaseModel):
    response: str

class FeedbackRequest(BaseModel):
    history: list
    scenario_id: str

class FeedbackResponse(BaseModel):
    feedback: str

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serves the main HTML page."""
    index_html_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_html_path):
        return FileResponse(index_html_path)
    raise HTTPException(status_code=404, detail="index.html not found.")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    user_message = request.message
    scenario_id = request.scenario_id

    # Initialize variables to prevent UnboundLocalError
    customer_response_text: str = "An error occurred in the chat."
    goals_answered: List[bool] = []

    # Validate scenario_id
    if scenario_id not in scenarios_data:
        print(f"ERROR_BACKEND: Invalid scenario_id received: {scenario_id}")
        raise HTTPException(status_code=400, detail="Invalid scenario selected.")

    selected_scenario = scenarios_data[scenario_id]

    current_chat_session: gemini_chat_service.GeminiChatSession # Type hint for clarity

    if session_id not in chat_sessions:
        try:
            customer_name = selected_scenario['customerName']
            customer_backstory = selected_scenario['backstory']
            customer_tone = selected_scenario['tone']
            customer_goal_questions = selected_scenario['goalQuestions']
            print(f"DEBUG_BACKEND: Scenario persona details successfully retrieved from scenarios.json.")
        except KeyError as e:
            print(f"ERROR_BACKEND: Missing expected key in scenarios.json for scenario '{scenario_id}': '{e}'. Please check your scenarios.json structure.")
            raise HTTPException(status_code=500, detail=f"Server configuration error: Incomplete scenario data for ID '{scenario_id}'. Missing key: {e}")

        # Initialize a new chat session for this user, passing individual parameters
        chat_sessions[session_id] = gemini_chat_service.GeminiChatSession(
            name=customer_name, # Pass the extracted customerName
            session_id=session_id,
            backstory=customer_backstory, # Pass the extracted backstory
            tone=customer_tone, # Pass the extracted tone
            goal_questions=customer_goal_questions # Pass the extracted goal_questions
        )
        print(f"DEBUG_BACKEND: Creating new chat session for session_id: {session_id} with scenario: {scenario_id}")

        # For the very first message in a new session, send a generic prompt
        # from the customer service side to initiate the AI customer's response (first goal question).
        initial_response_data = await chat_sessions[session_id].send_message(
            customer_service_response="Hello, I am ready to start the chat."
        )
        customer_response_text = initial_response_data["ai_response"]
        goals_answered = initial_response_data["goals_answered"] # Capture the goals_answered list
        print(f"DEBUG_BACKEND: Initial customer response from AI: {customer_response_text[:200]}...")

    else:
        current_chat_session = chat_sessions[session_id]
        print(f"DEBUG_BACKEND: Resuming chat session: {session_id}")
        # Get the AI's response based on the user's message
        response_data = await current_chat_session.send_message(customer_service_response=user_message)
        customer_response_text = response_data["ai_response"]
        goals_answered = response_data["goals_answered"] # Capture the goals_answered list
        print(f"DEBUG_BACKEND: Received Gemini API response (first 200 chars): {customer_response_text[:200]}...")

    # The goal tracking logic is now fully handled within gemini_chat_service.py's send_message and _update_goal_status.
    # The 'goals_answered' variable is populated from the response_data.
    print(f"DEBUG_BACKEND: Goals answered status: {goals_answered}") 

    return ChatResponse(response=customer_response_text)

# Feedback endpoint
@app.post("/feedback", response_model=FeedbackResponse)
async def feedback_endpoint(request: FeedbackRequest):
    scenario_id = request.scenario_id
    conversation_history = request.history

    # Ensure the scenario is valid
    if scenario_id not in scenarios_data:
        raise HTTPException(status_code=400, detail="Invalid scenario selected for feedback.")

    selected_scenario = scenarios_data[scenario_id]

    print(f"DEBUG_BACKEND: Received feedback request for scenario ID: {scenario_id}")

    # The feedback logic will be handled by a new function in gemini_chat_service
    try:
        feedback_text = await gemini_chat_service.get_feedback_from_model(
            history=conversation_history,
            scenario_details=selected_scenario
        )
        print("DEBUG_BACKEND: Successfully received feedback from model.")
        return FeedbackResponse(feedback=feedback_text)
    except Exception as e:
        print(f"ERROR_BACKEND: Failed to get feedback from model: {e}")
        raise HTTPException(status_code=500, detail="Failed to get feedback from the AI model.")
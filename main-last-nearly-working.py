from fastapi import FastAPI, HTTPException # Make sure HTTPException is imported
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uuid
import json
from typing import Dict
from typing import Dict, List # Import List here

# Assuming gemini_chat_service.py is in the same directory
import gemini_chat_service # The chat logic, including GeminiChatSession

# Define the path to your frontend directory (adjust "Frontend" if your folder is "frontend")
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "Frontend")

app = FastAPI()

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
    print(f"DEBUG_BACKEND: Loaded {len(scenarios_data)} scenarios from {scenarios_file_path}. Keys: {list(scenarios_data.keys())}")
else:
    print(f"ERROR_BACKEND: scenarios.json not found at {scenarios_file_path}")
    # You might want to raise an error or handle this more robustly in production
    raise RuntimeError(f"Required file scenarios.json not found at {scenarios_file_path}")


# Pydantic model for the chat request
class ChatRequest(BaseModel):
    message: str
    session_id: str
    scenario_id: str # This should be a string to match JavaScript


# Pydantic model for the chat response
class ChatResponse(BaseModel):
    response: str
    goals_answered: bool = False # Optional, for tracking goal completion


@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    user_message = request.message
    scenario_id = request.scenario_id

    print(f"DEBUG_BACKEND: Received chat request - Session ID: '{session_id}', Scenario ID: '{scenario_id}', Message: '{user_message}'")
    #goals_answered: List[bool] = []

    if scenario_id not in scenarios_data:
        print(f"ERROR_BACKEND: Invalid scenario_id: '{scenario_id}'. Available scenario IDs: {list(scenarios_data.keys())}")
        raise HTTPException(status_code=400, detail=f"Invalid scenario_id provided: {scenario_id}")

    selected_scenario = scenarios_data[scenario_id]
    print(f"DEBUG_BACKEND: Selected scenario title: {selected_scenario.get('title', 'N/A')}")

    # Initialize chat session if it's new
    if session_id not in chat_sessions:
        print(f"DEBUG_BACKEND: Creating new chat session for session_id: {session_id} with scenario: {scenario_id}")
        try:
            # Ensure these keys exist in your scenarios.json for the selected scenario
            customer_name = selected_scenario['customerName']
            customer_backstory = selected_scenario['backstory']
            customer_tone = selected_scenario['tone']
            customer_goal_questions = selected_scenario['goalQuestions']
            print(f"DEBUG_BACKEND: Scenario persona details successfully retrieved from scenarios.json.")
        except KeyError as e:
            print(f"ERROR_BACKEND: Missing expected key in scenarios.json for scenario '{scenario_id}': '{e}'. Please check your scenarios.json structure.")
            raise HTTPException(status_code=500, detail=f"Server configuration error: Incomplete scenario data for ID '{scenario_id}'. Missing key: {e}")

        chat_sessions[session_id] = gemini_chat_service.GeminiChatSession(
            name=customer_name,
            session_id=session_id,
            backstory=customer_backstory,
            tone=customer_tone,
            goal_questions=customer_goal_questions,  
        )
        # For the very first message in a new session, send a generic prompt
        # from the customer service side to initiate the AI customer's response (first goal question).
        initial_response_data = await chat_sessions[session_id].send_message(
            customer_service_response="Hello, I am ready to start the chat."
        )
        customer_response_text = initial_response_data["ai_response"]
        # The 'goals_answered' status is now handled internally by GeminiChatSession and returned by send_message.
        # We can capture it if needed for further backend logic or sending to frontend.
        goals_answered = initial_response_data["goals_answered"] # Capture the goals_answered list
        print(f"DEBUG_BACKEND: Initial customer response from AI: {customer_response_text[:200]}...")



        current_chat_session = chat_sessions[session_id]
        print(f"DEBUG_BACKEND: Creating new chat session for session_id: {session_id} with scenario: {scenario_id}")
        #chat_sessions[session_id] = new_chat_session
        print(f"DEBUG_BACKEND: Resuming chat session: {session_id}")
        # Get the AI's response based on the user's message
        response_data = await current_chat_session.send_message(customer_service_response=user_message)
        customer_response_text = response_data["ai_response"]
        goals_answered = response_data["goals_answered"] # Capture the goals_answered list
        print(f"DEBUG_BACKEND: Received Gemini API response (first 200 chars): {customer_response_text[:200]}...")

        
    else:
        print(f"DEBUG_BACKEND: Continuing existing chat session: {session_id} for scenario: {scenario_id}")

    current_chat_session = chat_sessions[session_id]

  

    return ChatResponse(response=customer_response_text, goals_answered=goals_answered)
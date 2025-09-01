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

# Chat endpoint for ongoing conversations
@app.post("/chat")
async def chat(request: ChatRequest):
    print(f"DEBUG_BACKEND: Received chat request for session ID: {request.session_id}")

    # Check if the session exists
    if request.session_id not in chat_sessions:
        # If no session, it means the user skipped the /start_chat endpoint
        raise HTTPException(status_code=400, detail="Chat session not found. Please start a new chat.")

    try:
        session = chat_sessions[request.session_id]
        
        # Send the user's message to the existing chat session
        response_data = await session.send_message(customer_service_response=request.message)
        
        customer_response_text = response_data["ai_response"]
        goals_answered = response_data["goals_answered"]
        
        print(f"DEBUG_BACKEND: Received Gemini API response (first 200 chars): {customer_response_text[:200]}...")
        print(f"DEBUG_BACKEND: Goals answered status: {goals_answered}")

        return {"response": customer_response_text}

    except Exception as e:
        print(f"ERROR_BACKEND: Failed to get AI response: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get AI response: {e}")

# Pydantic model for the start chat request
class StartChatRequest(BaseModel):
    session_id: str
    scenario_id: str

@app.post("/start_chat")
async def start_chat(request: StartChatRequest):
    print(f"DEBUG_BACKEND: Received start_chat request for session ID: {request.session_id}")
    try:
        if request.scenario_id not in scenarios_data:
            raise HTTPException(status_code=404, detail="Scenario not found.")

        scenario_details = scenarios_data[request.scenario_id]

        # Create a new chat session
        session = gemini_chat_service.GeminiChatSession(
            name=scenario_details["customerName"],
            session_id=request.session_id,
            backstory=scenario_details["backstory"],
            tone=scenario_details["tone"],
            goal_questions=scenario_details["goalQuestions"]
        )
        chat_sessions[request.session_id] = session

        # Get the initial response from the AI
        initial_response_data = await session.start_new_chat_session()

        return {"response": initial_response_data["ai_response"]}

    except Exception as e:
        print(f"ERROR_BACKEND: Failed to start chat session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start chat session: {e}")

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
from fastapi import FastAPI, HTTPException # Make sure HTTPException is imported
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uuid
import json
from typing import Dict, List, Any 
import asyncio # Import asyncio if not already present
from fastapi.middleware.cors import CORSMiddleware

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

# In-memory store for scenarios data
scenarios_data: Dict[str, dict] = {}
scenarios_file_path = os.path.join(FRONTEND_DIR, "scenarios.json")

def reload_scenarios():
    """Loads scenarios from the JSON file into memory."""
    global scenarios_data
    try:
        with open(scenarios_file_path, 'r', encoding='utf-8') as f:
            scenarios_list = json.load(f)
            scenarios_data.clear()  # Clear existing data before reloading
            for scenario in scenarios_list:
                scenarios_data[scenario['id']] = scenario
        print("Scenarios reloaded successfully.")
    except FileNotFoundError:
        print(f"ERROR: scenarios.json not found at {scenarios_file_path}")
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON format in {scenarios_file_path}")

# Load scenarios on startup
reload_scenarios()

# Pydantic model for the new scenario data
class ChatActor(BaseModel):
    customerName: str
    backstory: str
    tone: str
    goalQuestions: List[str]

class NewScenario(BaseModel):
    id: str
    title: str
    initialFacts: str
    chatActor: ChatActor


# Endpoint to add a new scenario
@app.post("/add_scenario")
async def add_scenario(scenario: NewScenario):
    print("DEBUG_BACKEND: Received request to add a new scenario.")
    try:
        # Load existing scenarios
        with open(scenarios_file_path, 'r', encoding='utf-8') as f:
            scenarios_list = json.load(f)

        # Append the new scenario
        scenarios_list.append(scenario.dict())

        # Save the updated list back to the file
        with open(scenarios_file_path, 'w', encoding='utf-8') as f:
            json.dump(scenarios_list, f, indent=4)

        # Reload scenarios into memory to make the new one available
        reload_scenarios()

        return {"message": f"Scenario '{scenario.title}' added successfully!"}

    except Exception as e:
        print(f"ERROR_BACKEND: Failed to add new scenario: {e}")
        raise HTTPException(status_code=500, detail="Failed to add new scenario.")

# Endpoint to export scenarios.json content. Open https://app-name/export_scenarios to download the file. 
@app.get("/export_scenarios")
async def export_scenarios():
    """Returns the contents of scenarios.json for local use."""
    try:
        with open(scenarios_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="scenarios.json not found on server.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid JSON format in scenarios.json.")


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

        if "chatActor" not in scenario_details:
            raise HTTPException(status_code=400, detail="Invalid scenario data. 'chatActor' key is missing.")

        # Create a new chat session
        session = gemini_chat_service.GeminiChatSession(
            session_id=request.session_id,
            chat_actor=scenario_details["chatActor"]
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

    if 'chatActor' not in selected_scenario:
        raise HTTPException(status_code=400, detail="Invalid scenario data. 'chatActor' key is missing.")

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
from fastapi import FastAPI

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

# Initialize the FastAPI application
app = FastAPI()

#Supa integration

# --- Supabase Configuration ---
# Ensure these environment variables are set in your .env file:
# SUPABASE_URL="YOUR_SUPABASE_URL"
# SUPABASE_KEY="YOUR_SUPABASE_ANON_KEY"
supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Supabase URL and Key must be set as environment variables.")

# Initialize the Supabase client
# Use the synchronous client for simplicity in this example,
# though supabase-py-async is available for async operations.
supabase: Client = create_client(supabase_url, supabase_key)

# --- Pydantic Model for Interaction Data ---
class Interaction(BaseModel):
    id: str | None = None # Supabase will generate this if not provided
    message: str
    user_id: str | None = None # Example field for user identification

# --- FastAPI Endpoints ---
@app.get("/")
async def read_root():
    """
    Root endpoint that returns a simple "Hello World" message.
    """
    return {"message": "Hello World - FastAPI with Supabase Integration"}

# To run this application:
# 1. Save the code as main.py
# 2. Install FastAPI and Uvicorn: pip install fastapi "uvicorn[standard]"
# 3. Run the application from your terminal: uvicorn main:app --reload
# 4. Open your browser and go to http://127.0.0.1:8000/ to see "Hello World".
# 5. You can also visit http://127.0.0.1:8000/docs for the interactive API documentation (Swagger UI).



@app.post("/user_interactions/")
async def create_interaction(interaction: Interaction):
    """
    Creates a new dummy interaction in the Supabase database.
    """
    try:
        # Insert data into the 'user_interactions' table
        # Make sure you have a table named 'interactions' in your Supabase project
        # with 'message' and 'user_id' columns.
        response = supabase.table("user_interactions").insert(interaction.model_dump(exclude_unset=True)).execute()
        # The data is in response.data for successful inserts
        if response.data:
            return {"status": "success", "data": response.data[0]}
        else:
            # Handle cases where data might be empty even if no error was raised
            raise HTTPException(status_code=500, detail="Failed to create interaction: No data returned.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create interaction: {e}")

@app.get("/user_interactions/")
async def get_interactions():
    """
    Retrieves all dummy interactions from the Supabase database.
    """
    try:
        response = supabase.table("user_interactions").select("*").execute()
        if response.data:
            return {"status": "success", "data": response.data}
        else:
            return {"status": "success", "data": []} # Return empty list if no data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve interactions: {e}")

@app.get("/user_interactions/{interaction_id}")
async def get_interaction(interaction_id: str):
    """
    Retrieves a single interaction by its ID from the Supabase database.
    """
    try:
        response = supabase.table("user_interactions").select("*").eq("id", interaction_id).execute()
        if response.data:
            if response.data:
                return {"status": "success", "data": response.data[0]}
            else:
                raise HTTPException(status_code=404, detail="Interaction not found.")
        else:
            raise HTTPException(status_code=404, detail="Interaction not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve interaction: {e}")

@app.put("/user_interactions/{interaction_id}")
async def update_interaction(interaction_id: str, interaction: Interaction):
    """
    Updates an existing interaction in the Supabase database.
    """
    try:
        # Update data in the 'user_interactions' table where id matches
        response = supabase.table("user_interactions").update(interaction.model_dump(exclude_unset=True)).eq("id", interaction_id).execute()
        if response.data:
            if response.data:
                return {"status": "success", "data": response.data[0]}
            else:
                raise HTTPException(status_code=404, detail="Interaction not found or no changes made.")
        else:
            raise HTTPException(status_code=404, detail="Interaction not found or no changes made.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update interaction: {e}")

@app.delete("/user_interactions/{interaction_id}")
async def delete_interaction(interaction_id: str):
    """
    Deletes an interaction from the Supabase database.
    """
    try:
        # Delete data from the 'user_interactions' table where id matches
        response = supabase.table("user_interactions").delete().eq("id", interaction_id).execute()
        if response.data:
            if response.data:
                return {"status": "success", "message": f"Interaction {interaction_id} deleted successfully."}
            else:
                raise HTTPException(status_code=404, detail="Interaction not found or already deleted.")
        else:
            raise HTTPException(status_code=404, detail="Interaction not found or already deleted.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete interaction: {e}")

# --- Instructions to Run ---
# 1. Save this code as main.py
# 2. Install necessary libraries:
#    pip install fastapi "uvicorn[standard]" python-dotenv supabase-py
# 3. Create a .env file in the same directory as main.py with your Supabase credentials:
#    SUPABASE_URL="YOUR_SUPABASE_URL"
#    SUPABASE_KEY="YOUR_SUPABASE_ANON_KEY"
#    (Replace YOUR_SUPABASE_URL and YOUR_SUPABASE_ANON_KEY with your actual credentials from Supabase project settings -> API)
# 4. In your Supabase project, create a table named 'interactions' with at least the following columns:
#    - id (text, Primary Key, Default Value: uuid_generate_v4() or similar for auto-generation)
#    - message (text)
#    - user_id (text, nullable)
# 5. Run the application from your terminal: uvicorn main:app --reload
# 6. Open your browser and go to http://127.0.0.1:8000/docs to interact with the API.

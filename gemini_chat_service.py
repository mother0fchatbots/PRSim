import time
import random
from typing import List, Dict, Any
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    print("Please set your Gemini API key as an environment variable or uncomment and update the script.")
    # In a production environment, you might raise an exception or exit here
else:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        # Consider making GOOGLE_API_KEY = None if config fails to prevent subsequent API calls

# Initialize the Gemini model
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

# --- Removed the top-level get_gemini_response function as it's now handled by the class ---
# Also removed MockGeminiAPI as you're using real Gemini API calls.

class GeminiChatSession:
    """
    Manages a single chat session with the Gemini model, acting as a customer
    trying to achieve specific goals.
    """

    def __init__(self, session_id: str, chat_actor: Dict[str, Any]):
        """
        Initializes the chat session with its persona and goals.

        Args:
            session_id (str): A unique ID for this chat session.
            backstory (str): The backstory/context for the AI customer.
            tone (str): The desired tone of the AI customer (e.g., "polite", "frustrated", "neutral").
            goal_questions (List[str]): A list of questions the AI customer needs to ask/get answers for.
        """
        self.session_id = session_id
        self.name = chat_actor["customerName"]
        self.backstory = chat_actor["backstory"]
        self.tone = chat_actor["tone"]
        self.goal_questions = chat_actor["goalQuestions"]
        self.goals_answered: List[bool] = [False] * len(self.goal_questions)
        self.chat_history: List[Dict[str, str]] = []
        self.current_question_index = 0 # Helps guide which question to ask next if not answered
        self.asked_questions = set()
        # print(f"Session {self.session_id} initialized. Goals: {self.goal_questions}")

    async def start_new_chat_session(self):
        """
        Starts a new chat session by sending a system instruction to the model
        and retrieving the first message from the AI.
        """
        initial_prompt = (
            f"You are a customer with the following backstory: {self.backstory}. "
            f"Your tone is {self.tone}. "
            #f"Your long-term goal is to get information about the following topics: {', '.join(self.goal_questions)}. "
            "Your goal is to get more information from the PR agent."
            "Please start the conversation. Just give your first message to the agent."
        )

        initial_response = await self._call_gemini_api(prompt=initial_prompt)

        self.chat_history.append({"role": self.name, "text": initial_response})
        
        # We process the response to get the initial AI message and check goals
        return {
            "ai_response": initial_response,
            "goals_answered": self.goals_answered # Return the boolean list
        }

    async def _call_gemini_api(self, prompt: str) -> str:
        """
        Calls the actual Gemini API to generate a response.
        """
        # Simulate network delay for a more realistic feel in a demo
        time.sleep(random.uniform(0.1, 0.5)) # Reduced delay for web interaction

        if not GOOGLE_API_KEY:
            print("Gemini API key is not set. Cannot make API call.")
            return "AI service is not available (API key missing)."

        try:
            # Use the actual Gemini API call
            # For multi-turn conversations, you might want to use model.start_chat()
            # and pass history, but for this structured prompt approach, generate_content works.
            response = await gemini_model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API for session {self.session_id}: {e}")
            return "I'm sorry, I'm having trouble connecting to the AI right now. Please try again later."

    def _construct_prompt(self, last_customer_service_response: str = "") -> str:
        """
        Constructs the prompt for the Gemini model to generate the AI customer's next message.
        Incorporates the AI customer's persona, chat history, and current goal status.

        Args:
            last_customer_service_response (str): The most recent message from the human user (Customer Service).

        Returns:
            str: The complete prompt string for the Gemini model.
        """
        prompt = f"You are a customer named '{self.name}'. Your backstory is: '{self.backstory}'.\n"
        prompt += f"Your current goal is to get answers to the following questions: {'; '.join(self.goal_questions)}.\n"
        prompt += f"Maintain a {self.tone} tone throughout the conversation.\n"
        prompt += "Simulate a conversation with a public relationship representative regarding the issue provided in a backstory. Do not break character."
        prompt += "Your responses should be concise and directly address the conversation flow. Use a natural, causal language to make conversation more realistic. \n"

        # Add chat history
        if self.chat_history:
            prompt += "\n--- Conversation History ---\n"
            for entry in self.chat_history:
                prompt += f"{entry['role']}: {entry['text']}\n"
            prompt += "--------------------------\n"

        # Add the latest customer service response if available
        if last_customer_service_response:
            prompt += f"Customer Service: {last_customer_service_response}\n"

        # Guidance for the AI based on goals
        unanswered_goals = [self.goal_questions[i] for i, answered in enumerate(self.goals_answered) if not answered]

        if unanswered_goals:
            # Prioritize asking unanswered questions if the current one hasn't been addressed
            if self.current_question_index < len(self.goal_questions) and not self.goals_answered[self.current_question_index]:
                prompt += f"Your next action: Ask the question: '{self.goal_questions[self.current_question_index]}'.\n"
                prompt += "Formulate your response as the customer asking this specific question, maintaining your tone.\n"
            else:
                # If current question is answered or index out of bounds, try to find the next unanswered one
                for i, answered in enumerate(self.goals_answered):
                    if not answered:
                        self.current_question_index = i # Move pointer to next unanswered goal
                        prompt += f"Your next action: Ask the question: '{self.goal_questions[self.current_question_index]}'.\n"
                        prompt += "Formulate your response as the customer asking this specific question, maintaining your tone.\n"
                        break
                else:
                    # Fallback if somehow all goals are true but loop didn't catch, or just engage
                    prompt += "Your next action: You have asked all your questions, but are you satisfied with the answers? Respond to the last customer service message, or conclude the conversation politely.\n"
        else:
            prompt += "Your next action: You have received answers to all your questions. End the chat politely and professionally.\n"

        prompt += "Your response (as the customer):"
        return prompt

    def _update_goal_status(self, customer_service_response: str):
        """
        Checks the customer service response against the goal questions
        and updates the `goals_answered` status.
        """
        for i, goal_q in enumerate(self.goal_questions):
            if not self.goals_answered[i]: # Only check if not already answered
                # Simple keyword matching for demo. In real scenario, use NLP.
                keywords = goal_q.lower().split()
                if any(keyword in customer_service_response.lower() for keyword in keywords if len(keyword) > 3): # Avoid very short common words
                    self.goals_answered[i] = True
                    # print(f"[DEBUG: Session {self.session_id}]: Goal '{goal_q}' marked as answered.")

    async def send_message(self, customer_service_response: str) -> Dict[str, any]:
        """
        Processes a message from the human user (Customer Service) and generates the
        AI customer's response.

        Args:
            customer_service_response (str): The message from the human user.

        Returns:
            Dict[str, any]: A dictionary containing the AI customer's response and
                            the current status of goals answered.
        """
        # 1. Add human user's message to history
        self.chat_history.append({"role": "Customer Service", "text": customer_service_response})

        # 2. Update goal status based on human user's response
        self._update_goal_status(customer_service_response)

        # 3. Construct prompt for AI customer's response
        prompt = self._construct_prompt(customer_service_response)

        # 4. Get AI customer's response from Gemini
        ai_customer_message = await self._call_gemini_api(prompt)

        # 5. Add AI customer's response to history
        self.chat_history.append({"role": self.name, "text": ai_customer_message})

        # 6. Return response and goal status
        return {
            "ai_response": ai_customer_message,
            "goals_answered": self.goals_answered # Return the boolean list
        }

#feedback handler   
async def get_feedback_from_model(history: list, scenario_details: dict) -> str:
    print(f"DEBUG_SERVICE: Starting get_feedback_from_model...")
    if not GOOGLE_API_KEY:
        return "Unable to provide feedback: Gemini API key is not configured."
    
    try:
        customer_details = scenario_details['chatActor']
    except KeyError:
        return "Feedback could not be generated. Scenario data is missing the 'chatActor' key."

    prompt = (
        f"You are an expert PR and communications consultant tasked with evaluating a user's performance in a simulated PR crisis chat. "
        f"Your role is to provide constructive feedback based on the following conversation and scenario details. "
        f"The user's goal was to address all of the customer's concerns, which are listed as 'goalQuestions'.\n\n"
        f"--- Scenario Details ---\n"
        f"Customer Name: {customer_details['customerName']}\n"
        f"Customer Backstory: {customer_details['backstory']}\n"
        f"Customer Tone: {customer_details['tone']}\n"
        f"Customer's Goals (questions the user needed to address): {customer_details['goalQuestions']}\n\n"
        f"--- Conversation Transcript ---\n"
    )

    for message in history:
        sender_label = "User (Customer Service)" if message['sender'] == 'user' else f"{customer_details['customerName']} (Customer Bot)"
        prompt += f"{sender_label}: {message['text']}\n"

    prompt += (
        f"\n--- Feedback Request ---\n"
        f"Please provide your feedback using the exact following structure. Each section must be on a new line.\n"
        f"Start with a summary of the user's overall performance.\n\n"
        f"**Goal Achievement**\n"
        f"Did the user successfully address all of the customer's goal questions? List which ones were addressed and which were missed.\n\n"
        f"**Tone and Empathy**\n"
        f"Was the user's tone appropriate for a PR crisis? Did they sound empathetic and professional?\n\n"
        f"**Strategy**\n"
        f"Did the user seem to have a clear strategy or did they react impulsively? What was their overall effectiveness?\n\n"
        f"**Areas for Improvement**\n"
        f"Provide specific, actionable advice on how the user could have handled the conversation better. Suggest better phrasing or strategic approaches.\n"
    )

    print(f"DEBUG_SERVICE: Generated prompt for feedback:\n{prompt}")

    try:
        response = await gemini_model.generate_content_async(prompt)
        if hasattr(response, 'text'):
            # This is the key change: Split the text into lines and join with a newline character.
            # This handles cases where the model provides no line breaks.
            formatted_feedback = '\n'.join(line.strip() for line in response.text.split('.'))

            # The code below is a better way to format, so I am going to use that instead.
            # This is to handle any markdown formatting from the AI
            # We will use this to format the text
            formatted_feedback = response.text
            return formatted_feedback
            
        else:
            print(f"Error: Gemini API response did not contain a text attribute.")
            return "Failed to get a valid response from the AI model."
    except Exception as e:
        print(f"Error calling Gemini API for feedback: {e}")
        return "An error occurred while communicating with the AI model."

async def analyze_post_sentiment(post_title, post_content, scenario_details):
    """
    Semtiment analysis for a social media post
    
    """
    initial_facts = scenario_details['initialFacts']
    scenario_title = scenario_details['title']

     # Construct a detailed prompt for the Gemini model
    prompt = f"""
        **Context:** You are a social media sentiment analysis expert. Your task is to analyze a social media post and predict the sentiment of the audience.
        
        **Scenario Details:**
        - **Crisis:** {scenario_title}
        - **Initial Facts:** {initial_facts}
        - **Target Audience:** The general public, brand followers, and media.

        **Social Media Post to Analyze:**
        **Title:** {post_title}
        **Content:** {post_content}

        **Your Task:**
        Based on the provided context and the social media post content, provide a concise sentiment analysis. Specifically, answer the following questions:
        1.  **Overall Sentiment:** What is the overall sentiment of the post's content?
        2.  **Predicted Audience Reaction:** Given the crisis context, what sentiment or reaction will the target audience likely have after reading this post?
        3.  **Suggestions:** Briefly suggest a single, specific improvement to the post to achieve a more positive or neutral reaction.
        
        Format your response as a simple, easy-to-read summary. Do not include any preambles or conversational text.
        """
    
    try:
        response = await gemini_model.generate_content_async(prompt)
        if hasattr(response, 'text'):
            return response.text
        else:
            print(f"Error: Gemini API response did not contain a text attribute.")
            return "Failed to get a valid response from the AI model."
    except Exception as e:
        print(f"Error calling Gemini API for feedback: {e}")
        return "An error occurred while communicating with the AI model."


# --- This part is for direct testing of the service. It won't be run by FastAPI ---
if __name__ == "__main__":
    load_dotenv() # Ensure .env is loaded for testing

    # Test the get_gemini_response directly if needed (single turn)
    # This is less relevant now that we have sessions, but kept for legacy.
    # print("Testing get_gemini_response directly:")
    # test_message = "What is the capital of France?"
    # response = get_gemini_response(test_message) # This function no longer exists
    # print(f"User: {test_message}")
    # print(f"AI: {response}")

    # Test GeminiChatSession
    print("\n--- Testing GeminiChatSession directly ---")
    session_id_test = "test_session_123"
    test_backstory = "You are a new customer who needs help setting up your internet router."
    test_tone = "slightly confused but cooperative"
    test_goals = [
        "How do I connect the cables?",
        "What is the default Wi-Fi password?",
        "How do I change the Wi-Fi password?",
        "Is there a mobile app for management?"
    ]

    test_session = GeminiChatSession(
        session_id=session_id_test,
        name="Test Customer", # Name is used in prompt construction
        backstory=test_backstory,
        tone=test_tone,
        goal_questions=test_goals
    )

    async def run_test_chat():
        initial_ai_response = await test_session.send_message("Hello, how can I help you?")
        print(f"AI Customer: {initial_ai_response['ai_response']}")
        print(f"Goals: {test_session.goals_answered}")

        turn1_cs_response = "To connect the cables, please plug the power adapter into the router and wall outlet, and connect the Ethernet cable from your modem to the router's WAN port."
        turn1_result = await test_session.send_message(turn1_cs_response)
        print(f"AI Customer: {turn1_result['ai_response']}")
        print(f"Goals: {test_session.goals_answered}")

        turn2_cs_response = "The default Wi-Fi password is usually found on a sticker at the bottom of your router. Look for 'SSID' and 'Password'."
        turn2_result = await test_session.send_message(turn2_cs_response)
        print(f"AI Customer: {turn2_result['ai_response']}")
        print(f"Goals: {test_session.goals_answered}")

        turn3_cs_response = "You can change the Wi-Fi password by logging into the router's web interface, typically by typing 192.168.1.1 into your browser, then navigating to wireless settings."
        turn3_result = await test_session.send_message(turn3_cs_response)
        print(f"AI Customer: {turn3_result['ai_response']}")
        print(f"Goals: {test_session.goals_answered}")

        turn4_cs_response = "Yes, there is often a mobile app provided by the router manufacturer for easy management. Please check your router's documentation or the app store."
        turn4_result = await test_session.send_message(turn4_cs_response)
        print(f"AI Customer: {turn4_result['ai_response']}")
        print(f"Goals: {test_session.goals_answered}")

        turn5_cs_response = "You're very welcome! Is there anything else?"
        turn5_result = await test_session.send_message(turn5_cs_response)
        print(f"AI Customer: {turn5_result['ai_response']}")
        print(f"Goals: {test_session.goals_answered}")


    import asyncio
    asyncio.run(run_test_chat())
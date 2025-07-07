import time
import random
from typing import List, Dict
import google.generativeai as genai
import os
from dotenv import load_dotenv

# --- Simulate Gemini API Call ---
# In a real application, you would use the actual Gemini API client here.
# For this simulation, we'll use google_search as a placeholder to show
# where the API call would go.

# The `google_search` tool is used here as a placeholder for the Gemini API.
# In a real application, you would replace this with an actual call to the
# Gemini API, for example, using the Google Generative AI client library.

# Example of how a real Gemini API call might look (conceptual):
# from google.generativeai import GenerativeModel
# model = GenerativeModel('gemini-pro')
# response = model.generate_content(prompt)
# return response.text

google_api_key = os.environ.get("GOOGLE_API_KEY")

try:
    genai.configure(api_key=google_api_key)
except KeyError:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    print("Please set your Gemini API key as an environment variable or uncomment and update the script.")
    exit()

gemini_model = genai.GenerativeModel('gemini-1.5-flash')

class MockGeminiAPI:
    """
    A mock class to simulate the Gemini API's text generation.
    In a real application, this would be replaced by actual API calls.
    """
    def generate_content(self, prompt: str) -> str:
        """
        Simulates generating content based on a prompt.
        For demonstration, it will just return a predefined response or
        a simple acknowledgment.
        """
        print(f"\n[DEBUG: Mock Gemini API received prompt]: {prompt[:100]}...")
        # Simple logic to simulate responses based on keywords
        if "hello" in prompt.lower() or "hi" in prompt.lower():
            return "Hello! How can I assist you today?"
        elif "product" in prompt.lower() and "issue" in prompt.lower():
            return "I understand you're having an issue with a product. Please describe it in more detail."
        elif "warranty" in prompt.lower():
            return "Regarding your warranty, could you please provide the product's serial number or purchase date?"
        elif "refund" in prompt.lower():
            return "For refunds, we typically require proof of purchase and the reason for the return. What can I help you with specifically?"
        elif "thank you" in prompt.lower() or "thanks" in prompt.lower():
            return "You're welcome! Is there anything else I can help you with?"
        elif "all my questions" in prompt.lower() or "finished" in prompt.lower():
            return "Great! I'm glad I could help. Have a wonderful day!"
        else:
            return "I'm sorry, I didn't quite catch that. Could you please rephrase your question?"

#gemini_model = MockGeminiAPI()


class Chatbot:
    """
    A chatbot designed to simulate a customer interacting with customer service.
    It has a defined goal, tone, name, and backstory.
    """

    def __init__(self, name: str, backstory: str, tone: str, goal_questions: List[str]):
        """
        Initializes the chatbot with its persona and goal.

        Args:
            name (str): The fake name of the chatbot (customer).
            backstory (str): The backstory/context for the chatbot.
            tone (str): The desired tone of the conversation (e.g., "polite", "frustrated", "neutral").
            goal_questions (List[str]): A list of questions the chatbot needs to ask/get answers for.
        """
        self.name = name
        self.backstory = backstory
        self.tone = tone
        self.goal_questions = goal_questions
        self.asked_questions = set()  # To keep track of questions already asked
        self.chat_history: List[Dict[str, str]] = []
        self.current_question_index = 0
        print(f"Chatbot '{self.name}' initialized with tone: '{self.tone}' and goal: {self.goal_questions}")

    def _call_gemini_api(self, prompt: str) -> str:
        """
        Simulates calling the Gemini API to generate a response.
        In a real application, this would be an actual API call.

        Args:
            prompt (str): The prompt to send to the Gemini model.

        Returns:
            str: The generated response from the model.
        """
        # Simulate network delay
        time.sleep(random.uniform(0.5, 1.5))
        try:
            # This is where the actual Gemini API call would go.
            # For this example, we use the mock.
            response_text = gemini_model.generate_content(prompt)
            return response_text.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return "I'm sorry, I'm having trouble connecting right now. Please try again later."

    def _construct_prompt(self, customer_service_response: str = "") -> str:
        """
        Constructs the prompt for the Gemini model, incorporating the chatbot's
        persona, chat history, and the current customer service response.

        Args:
            customer_service_response (str): The last response from customer service.

        Returns:
            str: The complete prompt string.
        """
        # Start with the chatbot's persona
        prompt = f"You are {self.name}. Your backstory is: '{self.backstory}'.\n"
        prompt += f"Your current goal is to get answers to the following questions: {', '.join(self.goal_questions)}.\n"
        prompt += f"Maintain a {self.tone} tone throughout the conversation.\n"
        prompt += "Simulate a conversation with a customer service representative.\n"

        # Add chat history
        if self.chat_history:
            prompt += "\n--- Conversation History ---\n"
            for entry in self.chat_history:
                prompt += f"{entry['role']}: {entry['text']}\n"
            prompt += "--------------------------\n"

        # Add the latest customer service response if available
        if customer_service_response:
            prompt += f"Customer Service: {customer_service_response}\n"

        # Determine the next action based on goal and history
        if not self.is_goal_achieved():
            next_question = self.goal_questions[self.current_question_index]
            if next_question not in self.asked_questions:
                prompt += f"Your next action: Ask the question: '{next_question}'.\n"
                prompt += "Formulate your response as a customer asking this question, maintaining your tone.\n"
            else:
                # If the current question was already asked, try to move to the next
                self.current_question_index += 1
                if self.current_question_index < len(self.goal_questions):
                    next_question = self.goal_questions[self.current_question_index]
                    prompt += f"Your next action: Ask the question: '{next_question}'.\n"
                    prompt += "Formulate your response as a customer asking this question, maintaining your tone.\n"
                else:
                    prompt += "Your next action: You have asked all your questions. Conclude the conversation politely.\n"
        else:
            prompt += "Your next action: You have received answers to all your questions. End the chat politely.\n"

        prompt += "Your response (as the customer):"
        return prompt

    def is_goal_achieved(self) -> bool:
        """
        Checks if the chatbot has asked all its goal questions.
        In a more advanced scenario, this would also check if answers were satisfactory.
        """
        return len(self.asked_questions) == len(self.goal_questions)

    def start_chat(self, max_turns: int = 10):
        """
        Starts the simulated chat session.

        Args:
            max_turns (int): Maximum number of turns for the conversation.
        """
        print(f"\n--- Starting Chat Session for {self.name} ---")
        print(f"Chatbot Goal: {self.goal_questions}")
        print(f"Chatbot Tone: {self.tone}")
        print(f"Chatbot Backstory: {self.backstory}\n")

        customer_service_response = ""

        for turn in range(1, max_turns + 1):
            if self.is_goal_achieved():
                print(f"\n[{self.name}]: All questions asked. Concluding chat.")
                # Final prompt to say goodbye
                prompt = self._construct_prompt(customer_service_response)
                final_customer_response = self._call_gemini_api(prompt)
                print(f"[Customer Service]: {final_customer_response}")
                self.chat_history.append({"role": "Customer Service", "text": final_customer_response})
                break

            print(f"\n--- Turn {turn} ---")

            # Chatbot (Customer) generates its message
            prompt = self._construct_prompt(customer_service_response)
            customer_message = self._call_gemini_api(prompt)
            print(f"[{self.name}]: {customer_message}")
            self.chat_history.append({"role": self.name, "text": customer_message})

            # Simulate customer service processing the message
            time.sleep(random.uniform(0.5, 1.0))

            # --- MODIFICATION START ---
            # Now, instead of simulating, we ask for user input for customer service
            print("\n[Your Turn as Customer Service]: Please type your response below.")
            customer_service_response = input("Customer Service: ")
            # --- MODIFICATION END ---

            print(f"[Customer Service]: {customer_service_response}") # Echoing user input for clarity
            self.chat_history.append({"role": "Customer Service", "text": customer_service_response})

            # Check if the current question from the goal was addressed/asked
            if self.current_question_index < len(self.goal_questions):
                current_goal_q = self.goal_questions[self.current_question_index].lower()
                # We'll check if the user's response contains keywords from the goal question
                if any(keyword in customer_service_response.lower() for keyword in current_goal_q.split()):
                    self.asked_questions.add(self.goal_questions[self.current_question_index])
                    print(f"[DEBUG]: Question '{self.goal_questions[self.current_question_index]}' marked as asked/addressed.")
                    self.current_question_index += 1 # Move to the next question
                elif current_goal_q in customer_message.lower(): # Also check if the customer chatbot asked it
                    self.asked_questions.add(self.goal_questions[self.current_question_index])
                    print(f"[DEBUG]: Question '{self.goal_questions[self.current_question_index]}' marked as asked/addressed by chatbot.")
                    self.current_question_index += 1 # Move to the next question


        if not self.is_goal_achieved():
            print(f"\n--- Chat Session Ended (Max turns reached) ---")
            print(f"Goal not fully achieved. Remaining questions: {set(self.goal_questions) - self.asked_questions}")
        else:
            print(f"\n--- Chat Session Completed Successfully ---")
            print(f"All goal questions were addressed.")


# --- Example Usage ---
if __name__ == "__main__":
    # Define the chatbot's persona and goal
    customer_chatbot = Chatbot(
        name="Alice",
        backstory="Alice recently purchased a new smart home device and is having trouble connecting it to her Wi-Fi. She also has a question about its warranty.",
        tone="slightly frustrated but polite",
        goal_questions=[
            "How do I connect my smart home device to Wi-Fi?",
            "What is the warranty period for this device?",
            "Can I get a refund if it doesn't work after troubleshooting?"
        ]
    )

    # Start the simulated chat
    customer_chatbot.start_chat(max_turns=7)

#    print("\n--- Another Example: Bob, a happy customer ---")
#    happy_customer_chatbot = Chatbot(
#        name="Bob",
#        backstory="Bob just received his new gaming console and wants to know about recommended accessories and future game releases.",
#        tone="enthusiastic and curious",
#        goal_questions=[
#            "What are the best accessories for the new gaming console?",
#            "When can I expect new exclusive games to be released?",
#            "Are there any upcoming online multiplayer events?"
#        ]
#    )
#    happy_customer_chatbot.start_chat(max_turns=8)

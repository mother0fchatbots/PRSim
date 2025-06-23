import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Configure the Gemini API key
# It's recommended to set your API key as an environment variable (e.g., GOOGLE_API_KEY)
# For testing purposes, you can uncomment and replace with your actual key:
# os.environ["GOOGLE_API_KEY"] = "YOUR_GEMINI_API_KEY"

google_api_key = os.environ.get("GOOGLE_API_KEY")

try:
    genai.configure(api_key=google_api_key)
except KeyError:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    print("Please set your Gemini API key as an environment variable or uncomment and update the script.")
    exit()

def generate_crisis_scenario(client_industry, crisis_type, severity):
    """
    Generates a detailed PR crisis scenario using the Gemini API.

    Args:
        client_industry (str): The client or industry involved (e.g., "tech startup", "food and beverage", "healthcare").
        crisis_type (str): The type of crisis (e.g., "data breach", "product recall", "CEO misconduct").
        severity (str): The severity of the crisis ("low", "medium", "high", "critical").

    Returns:
        str: A detailed description of the crisis event, or an error message.
    """

    model = genai.GenerativeModel('gemini-1.5-flash') # Using gemini-1.5-flash for faster responses

    prompt = f"""
    Generate a highly realistic and detailed PR crisis event based on the following parameters:

    Client/Industry: {client_industry}
    Crisis Type: {crisis_type}
    Severity: {severity}

    The output should include the following sections:

    1.  **Crisis Title:** A concise and impactful title for the crisis.
    2.  **Initial Facts:**
        * Date and Time of initial event.
        * Location of initial event.
        * A brief, factual description of what happened, including any immediate known causes or triggers.
        * Any initial impact or consequences.
    3.  **Key Actors Involved:**
        * The company/client name (create a realistic-sounding name if not provided).
        * Specific individuals or departments within the company directly involved or responsible.
        * External parties (e.g., affected individuals, regulatory bodies, competitors, activist groups) who are significant to the crisis.
    4.  **Immediate Media Implications:**
        * How the news broke (e.g., social media, traditional news outlet, internal leak).
        * Initial sentiment on social media and traditional news.
        * Key hashtags or trending topics.
        * Examples of initial headlines or news snippets (both factual and sensationalized).
        * Any immediate calls to action or demands from the public or stakeholders.
    5.  **Severity Impact Justification:** Briefly explain how the generated scenario aligns with the specified severity level (low, medium, high, critical) in terms of potential reputational damage, financial loss, legal consequences, and public trust.

    Ensure the scenario is plausible and provides enough detail for a PR professional or student to begin formulating a response strategy.
    """

    try:
        response = model.generate_content(prompt)
        # Access the text from the GenerateContentResponse object
        if response.parts:
            return response.text
        else:
            return "Could not generate content. The response was empty."
    except Exception as e:
        return f"An error occurred while generating the crisis scenario: {e}"

def main():
    """
    Main function to run the PR crisis simulator console interface.
    """
    print("Welcome to the PR Crisis Simulator!")
    print("Let's generate a realistic crisis scenario for you.")

    while True:
        client_industry = input("\nEnter the client or industry (e.g., 'tech startup', 'airline', 'pharmaceutical company'): ").strip()
        crisis_type = input("Enter the type of crisis (e.g., 'data breach', 'product recall', 'CEO misconduct', 'environmental damage'): ").strip()
        severity = input("Enter the severity of the crisis ('low', 'medium', 'high', 'critical'): ").strip().lower()

        if not all([client_industry, crisis_type, severity]):
            print("All fields are required. Please try again.")
            continue

        if severity not in ['low', 'medium', 'high', 'critical']:
            print("Invalid severity. Please choose 'low', 'medium', 'high', or 'critical'.")
            continue

        print("\nGenerating crisis scenario, please wait...")
        scenario = generate_crisis_scenario(client_industry, crisis_type, severity)
        print("\n--- CRISIS SCENARIO GENERATED ---")
        print(scenario)
        print("---------------------------------")

        another = input("\nDo you want to generate another scenario? (yes/no): ").strip().lower()
        if another != 'yes':
            print("Thank you for using the PR Crisis Simulator. Goodbye!")
            break

if __name__ == "__main__":
    main()
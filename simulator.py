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
    
def generate_holding_statement(crisis_scenario_text):
    """
    Generates a professional holding statement based on the crisis scenario.

    Args:
        crisis_scenario_text (str): The detailed crisis event description from generate_crisis_scenario.

    Returns:
        str: A draft holding statement.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    Given the following PR crisis scenario, draft a concise and professional **Holding Statement**.

    A holding statement is an initial, brief public communication designed to:
    - Acknowledge the situation.
    - Show empathy (if applicable).
    - State that the company is actively investigating/addressing the issue.
    - Indicate that more information will follow.
    - Avoid speculation or blame.
    - Maintain trust and control the narrative in the immediate aftermath.

    Crisis Scenario:
    {crisis_scenario_text}

    ---
    **Draft Holding Statement:**
    """

    try:
        response = model.generate_content(prompt)
        if response.parts:
            return response.text
        else:
            return "Could not generate holding statement. The response was empty."
    except Exception as e:
        return f"An error occurred while generating the holding statement: {e}"

def generate_social_media_draft(crisis_scenario_text, holding_statement_text):
    """
    Generates an initial social media post draft based on the crisis scenario and holding statement.
    This post should aim to "buy time" and direct users to official channels.

    Args:
        crisis_scenario_text (str): The detailed crisis event description.
        holding_statement_text (str): The generated holding statement.

    Returns:
        str: A draft social media post (e.g., for Twitter/X, Facebook).
    """
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    Given the following PR crisis scenario and the drafted Holding Statement,
    create an initial social media post (suitable for platforms like Twitter/X or Facebook)
    that aims to "buy time" and direct users to official updates.

    The social media post should:
    - Be very brief and to the point.
    - Acknowledge the situation without going into excessive detail.
    - Express concern or empathy (if appropriate).
    - State that the company is actively investigating/working on it.
    - Direct users to a specified official channel (e.g., company website, official press release page) for future updates.
    - Use relevant but neutral hashtags.
    - Avoid speculation, blame, or promises that cannot yet be confirmed.

    Crisis Scenario:
    {crisis_scenario_text}

    ---
    Holding Statement (for context, do not copy verbatim):
    {holding_statement_text}

    ---
    **Draft Initial Social Media Post:**
    """

    try:
        response = model.generate_content(prompt)
        if response.parts:
            return response.text
        else:
            return "Could not generate social media draft. The response was empty."
    except Exception as e:
        return f"An error occurred while generating the social media draft: {e}"


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

        generate_statements_choice = input("\nDo you want to generate a Holding Statement and Initial Social Media Draft for this scenario? (yes/no): ").strip().lower()

        if generate_statements_choice == 'yes':
            print("\nGenerating Holding Statement, please wait...")
            holding_statement = generate_holding_statement(scenario)
            print("\n--- HOLDING STATEMENT DRAFT ---")
            print(holding_statement)
            print("---------------------------------")

            print("\nGenerating Initial Social Media Draft, please wait...")
            social_media_post = generate_social_media_draft(scenario, holding_statement)
            print("\n--- INITIAL SOCIAL MEDIA DRAFT ---")
            print(social_media_post)
            print("---------------------------------")
        else:
            print("Skipping statement generation.")


        another = input("\nDo you want to generate another scenario? (yes/no): ").strip().lower()
        if another != 'yes':
            print("Thank you for using the PR Crisis Simulator. Goodbye!")
            break

if __name__ == "__main__":
    main()
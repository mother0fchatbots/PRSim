document.addEventListener('DOMContentLoaded', () => {

    // --- New Login Form Selectors ---
    const loginSection = document.getElementById('login-section');
    const loginForm = document.getElementById('login-form');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const loginErrorMessage = document.getElementById('login-error-message');

    // --- View Containers ---
    const mainView = document.getElementById('main-view');
    const scenarioPage = document.getElementById('scenario-page');
    const navSidebar = document.getElementById('nav-sidebar');

    // --- Scenario Selection and Details ---
    const scenarioSelect = document.getElementById('scenario-select');
    const scenarioTitle = document.getElementById('scenario-title');
    const factsContent = document.getElementById('facts-content');
    const toggleDetailsBtn = document.getElementById('toggle-details-btn');
    const scenarioDetailsContent = document.getElementById('scenario-details-content');

    // --- Task List ---
    const startChatBtn = document.getElementById('start-chat-btn');
    const getFeedbackBtn = document.getElementById('get-feedback-btn');
    const chatActorBackstory = document.getElementById('chat-actor-backstory');
    const publishStatementBtn = document.getElementById('publish-statement-btn');
    const statementContainer = document.getElementById('statement-container');

    // --- Chat Elements ---
    const chatContainer = document.getElementById('chat-container');
    const closeChatBtn = document.getElementById('close-chat-btn');
    const chatInput = document.getElementById('chat-input');
    const sendChatBtn = document.getElementById('send-chat-btn');
    const chatBody = document.getElementById('chat-body');
    const chatCustomerNameElement = document.getElementById('chat-customer-name');

    // --- Feedback Elements ---
    const feedbackContainer = document.getElementById('feedback-container');
    const feedbackContent = document.getElementById('feedback-content');
    const closeFeedbackBtn = document.getElementById('close-feedback-btn');

    // New element selectors for the "Add Scenario" feature
    const viewScenariosLink = document.getElementById('view-scenarios-link');
    const addScenarioLink = document.getElementById('add-scenario-link');
    const addScenarioFormSection = document.getElementById('add-scenario-form-section');
    const scenarioForm = document.getElementById('scenario-form');

    // Dynamically determine the backend URL based on the environment
    const backendUrl = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:8000'
    : '';

    // --- State Variables ---
    let allScenarios = [];
    let currentSessionId = null;
    let currentScenarioId = null;
    let conversationHistory = [];

    // --- Hardcoded Credentials ---
    const AUTH_USERNAME = 'guest';
    const AUTH_PASSWORD = 'narrative123';
    const AUTH_FLAG = 'isAuthenticated';

    // --- Utility Functions ---
    function generateSessionId() {
        return 'session-' + Date.now();
    }

    // format the raw AI feedback text
    function formatFeedbackText(text) {
        if (!text) return '';

        // Split the text by the bolded headings. This is the key step.
        const parts = text.split(/\*\*(.*?)\*\*\s*\n/);
        let formattedText = '';

        for (let i = 0; i < parts.length; i++) {
            if (i % 2 === 1) { // This is a heading
                formattedText += `<h2>${parts[i]}</h2>`;
            } else { // This is the content below a heading, or the initial text
                // Replace newlines with <br> for proper line breaks
                let content = parts[i].replace(/\n/g, '<br>');
                // Also, replace a period and a space with a period and a line break.
                // This is a failsafe to handle cases where the model gives no line break.
                content = content.replace(/\.\s/g, '.<br>');
                formattedText += `<p>${content}</p>`;
            }
        }

        return formattedText;
    }

    function addMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        messageDiv.innerHTML = `<p>${message}</p>`;
        chatBody.appendChild(messageDiv);
        chatBody.scrollTop = chatBody.scrollHeight; // Auto-scroll to the latest message
    }

    function resetChat() {
        chatBody.innerHTML = '';
        currentSessionId = null;
        conversationHistory = [];
    }

    // --- View Management ---
    function showLoginView() {
        loginSection.style.display = 'block';
        mainView.style.display = 'none';
        scenarioPage.style.display = 'none';
        chatContainer.style.display = 'none';
        feedbackContainer.style.display = 'none';
        addScenarioFormSection.style.display = 'none';
        statementContainer.style.display = 'none';
        startChatBtn.style.display = 'none';
    }

    function showMainView() {
        loginSection.style.display = 'none';
        mainView.style.display = 'block';
        scenarioPage.style.display = 'none';
        chatContainer.style.display = 'none';
        feedbackContainer.style.display = 'none';
        startChatBtn.style.display = 'block';
        getFeedbackBtn.style.display = 'none';
        navSidebar.style.display = 'block';
    }

    function showScenarioPage() {
        mainView.style.display = 'none';
        scenarioPage.style.display = 'flex';
        chatContainer.style.display = 'none';
        feedbackContainer.style.display = 'none';
        addScenarioFormSection.style.display = 'none';
        scenarioDetailsContent.style.display = 'block'
    }

    function showChat() {
        chatContainer.style.display = 'flex';
        scenarioDetailsContent.style.display = 'none';
        toggleDetailsBtn.textContent = 'Show Details';
    }

    function hideChat() {
        chatContainer.style.display = 'none';
        scenarioDetailsContent.style.display = 'block';
        toggleDetailsBtn.textContent = 'Hide Details';
        getFeedbackBtn.style.display = 'block';
    }

    function showAddScenarioForm() {
        mainView.style.display = 'none';
        addScenarioFormSection.style.display = 'block';
        scenarioPage.style.display = 'none';
    }

    function showComposeStatementForm() {
        statementContainer.style.display = 'block';
        publishStatementBtn.style.display = 'none';}


    // --- Main Logic ---
    async function loadScenarios() {
        try {
            const response = await fetch(`${backendUrl}/static/scenarios.json`);
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            allScenarios = await response.json();
            populateDropdown(allScenarios);
        } catch (error) {
            console.error('Error loading scenarios:', error);
            // In a real app, display a user-friendly error message
        }
    }

    function populateDropdown(scenarios) {
        scenarios.forEach(scenario => {
            const option = document.createElement('option');
            option.value = scenario.id;
            option.textContent = scenario.title;
            scenarioSelect.appendChild(option);
        });
    }

    function renderScenarioDetails(scenario) {
        scenarioDetailsContent.style.display = 'block';
        scenarioTitle.textContent = scenario.title;
        factsContent.innerHTML = scenario.initialFacts;
        chatActorBackstory.innerHTML = `<strong>Customer Backstory:</strong> ${scenario.chatActor.backstory}`;

        // Reset and hide the chat and feedback sections when a new scenario is loaded
        resetChat();
        hideChat();
        feedbackContainer.style.display = 'none';
        startChatBtn.style.display = 'block';
        getFeedbackBtn.style.display = 'none';

        // Update the customer name in the chat header
        chatCustomerNameElement.textContent = scenario.chatActor.customerName;

        // Show the new scenario page
        showScenarioPage();
    }

    async function sendMessage() {
        const userMessage = chatInput.value.trim();
        if (userMessage) {
            addMessage(userMessage, 'user');
            conversationHistory.push({ sender: 'user', text: userMessage });
            chatInput.value = '';

            // If it's a new chat, generate a session ID
            if (!currentSessionId) {
                currentSessionId = generateSessionId();
            }

            try {
                const response = await fetch(`${backendUrl}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: userMessage,
                        session_id: currentSessionId,
                        scenario_id: currentScenarioId
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }

                const data = await response.json();
                addMessage(data.response, 'ai');
                conversationHistory.push({ sender: 'ai', text: data.response });
            } catch (error) {
                console.error('Error sending message to backend:', error);
                addMessage("I'm sorry, I encountered an error. Please try again.", 'ai');
            }
        }
    }

    // --- Event Listeners ---

    // --- Login Form ---
    loginForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const username = usernameInput.value;
        const password = passwordInput.value;

        if (username === AUTH_USERNAME && password === AUTH_PASSWORD) {
            localStorage.setItem(AUTH_FLAG, 'true');
            loginErrorMessage.classList.add('hidden');
            loadScenarios();
            showMainView();             
        } else {
            loginErrorMessage.textContent = 'Invalid username or password.';
            loginErrorMessage.classList.remove('hidden');
        }
    });

    // --- Left-hand menu ---
    // Scenario selection
    scenarioSelect.addEventListener('change', (event) => {
        currentScenarioId = event.target.value;
        const selectedScenario = allScenarios.find(s => s.id === currentScenarioId);
        if (selectedScenario) {
            renderScenarioDetails(selectedScenario);
        }
    });

    // "Add Scenario" menu item
    addScenarioLink.addEventListener('click', (event) => {
        event.preventDefault(); // Prevents the link from navigating

        // Hide the main view and show the form
        mainView.classList.add('hidden');
        showAddScenarioForm();
    });

    // Event listener for the "View Scenarios" menu item (to go back)
    viewScenariosLink.addEventListener('click', (event) => {
        event.preventDefault(); // Prevents the link from navigating

        // Show the main view and hide the form
        mainView.classList.remove('hidden');
        addScenarioFormSection.classList.add('hidden');
    });    

    // Toggle scenario details
    toggleDetailsBtn.addEventListener('click', () => {
        if (scenarioDetailsContent.style.display === 'none') {
            scenarioDetailsContent.style.display = 'block';
            toggleDetailsBtn.textContent = 'Hide Details';
        } else {
            scenarioDetailsContent.style.display = 'none';
            toggleDetailsBtn.textContent = 'Show Details';
        }
    });

    // Start chat button
    startChatBtn.addEventListener('click', async () => {
        resetChat();
        showChat();
        chatContainer.classList.add('open');
        startChatBtn.style.display = 'none';
        getFeedbackBtn.style.display = 'none';
        conversationHistory = []; // Clear the history for a new session
        
        currentScenarioId = scenarioSelect.value;
        const selectedScenario = allScenarios.find(s => s.id === currentScenarioId);

        if (!selectedScenario) {
            chatBody.innerHTML = `<div class="message welcome-message"><p>Please select a scenario to begin the chat.</p></div>`;
            return;
        }

        // Show a loading message while waiting for the AI
        chatBody.innerHTML = `<div class="message welcome-message"><p>Connecting to ${selectedScenario.chatActor.customerName}...</p></div>`;

        currentSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        console.log("New chat session ID generated:", currentSessionId);

        try {
            // New fetch call to a dedicated start_chat endpoint
            const response = await fetch(`${backendUrl}/start_chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: currentSessionId,
                    scenario_id: currentScenarioId
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP error! Status: ${response.status} - ${errorData.detail || response.statusText}`);
            }

            const data = await response.json();
            // Clear the loading message and display the AI's first message
            chatBody.innerHTML = ''; 
            addMessage(data.response, 'ai');

        } catch (error) {
            console.error('Error starting chat session:', error);
            chatBody.innerHTML = `<div class="message ai-message"><p>I'm sorry, I couldn't connect to the customer. Please try again.</p></div>`;
            startChatBtn.style.display = 'block';
            getFeedbackBtn.style.display = 'block';
        }
    });

    // Close chat button
    closeChatBtn.addEventListener('click', () => {
        hideChat();
    });

    // Send chat button
    sendChatBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });

    // Get feedback button
    getFeedbackBtn.addEventListener('click', async () => {
        if (conversationHistory.length > 0 && currentScenarioId) {
            feedbackContainer.style.display = 'flex';
            feedbackContent.innerHTML = '<p>Generating feedback... Please wait.</p>';

            try {
                const response = await fetch(`${backendUrl}/feedback`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        history: conversationHistory,
                        scenario_id: currentScenarioId
                    })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`HTTP error! Status: ${response.status} - ${errorData.detail || response.statusText}`);
                }

                const data = await response.json();
                //feedbackContent.innerHTML = data.feedback; 
                const formattedFeedback = formatFeedbackText(data.feedback);
                feedbackContent.innerHTML = formattedFeedback

            } catch (error) {
                console.error('Error requesting feedback from backend:', error);
                feedbackContent.innerHTML = `<p style="color: red;">Sorry, an error occurred while getting feedback: ${error.message}</p>`;
            }
        } else {
            alert("No conversation history to get feedback on.");
        }
    });

    // Close feedback button
    closeFeedbackBtn.addEventListener('click', () => {
        feedbackContainer.style.display = 'none';
        showMainView(); // Go back to the main view after closing feedback
        scenarioSelect.value = ""; // Reset the dropdown
    });

    // Compose statement button
    publishStatementBtn.addEventListener('click', () => {
        const selectedScenario = allScenarios.find(s => s.id === currentScenarioId);
        if (!selectedScenario) {
            alert("Please select a scenario first.");
            return;
        }

        showComposeStatementForm();
    });

    // Add new scenario form submission
    scenarioForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent the form from submitting normally

        // Collect data from the form
        const formData = new FormData(scenarioForm);
        const newScenario = {
            id: `scenario-${Date.now()}`,
            title: formData.get('scenario-title'),
            initialFacts: formData.get('initial-facts-content'),
            chatActor: {
                customerName: formData.get('customer-name'),
                backstory: formData.get('backstory'),
                tone: formData.get('tone'),
                goalQuestions: formData.get('goal-questions').split(',').map(item => item.trim())
            }
        };

        console.log("Data being sent to backend:", newScenario);

        try {
            // Send the new scenario data to the backend
            const response = await fetch(`${backendUrl}/add_scenario`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newScenario)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP error! Status: ${response.status} - ${errorData.detail || response.statusText}`);
            }

            const result = await response.json();
            alert(result.message);

            // Reload the scenarios from the server to get the new one
            await loadScenarios();
            
            // Clear the form and navigate back to the main view
            scenarioForm.reset();
            mainView.classList.remove('hidden');
            addScenarioFormSection.classList.add('hidden');

        } catch (error) {
            console.error('Error adding new scenario:', error);
            alert(`Failed to add scenario. Please check the console for details.`);
        }
    });    

    // Initial load
    //loadScenarios();
    //showMainView(); // Start on the welcome page

    //  --- Authentication Logic ---
    if (localStorage.getItem(AUTH_FLAG) === 'true') {
        loadScenarios();
        showMainView();
    } else {
        showLoginView();
    }
});
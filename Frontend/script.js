document.addEventListener('DOMContentLoaded', () => {
    const scenarioSelect = document.getElementById('scenario-select');
    const factsContent = document.getElementById('facts-content');
    const actorsContent = document.getElementById('actors-content');
    const implicationsContent = document.getElementById('implications-content');
    const justificationsContent = document.getElementById('justifications-content');

    // New Chat elements
    const startChatBtn = document.getElementById('start-chat-btn');
    const chatContainer = document.getElementById('chat-container');
    const closeChatBtn = document.getElementById('close-chat-btn');
    const chatInput = document.getElementById('chat-input');
    const sendChatBtn = document.getElementById('send-chat-btn');
    const chatBody = document.getElementById('chat-body'); // The messages display area

    let allScenarios = []; // To store all loaded scenarios
    let currentSessionId = null; 
    let currentScenarioId = null; 

    // Function to load scenarios from JSON
    async function loadScenarios() {
        try {
            const response = await fetch('/static/scenarios.json');
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            allScenarios = await response.json();
            console.log("DEBUG: scenarios.json loaded successfully. Number of scenarios:", allScenarios.length);
            populateDropdown(allScenarios);
            // Optionally, load the content for the first scenario by default on page load
            if (allScenarios.length > 0) {
                scenarioSelect.value = allScenarios[0].id;
                fillContent(allScenarios[0].id);
                console.log("DEBUG: Initial scenario selected via loadScenarios:", allScenarios[0].id);
            } else {
                console.warn("DEBUG: No scenarios found in scenarios.json, or array is empty.");
            }
        } catch (error) {
            console.error('Error loading scenarios:', error);
            factsContent.innerHTML = '<p style="color: red;">Error loading scenarios. Please check the console for details.</p>';
        }
    }

    // Function to populate the dropdown
    function populateDropdown(scenarios) {
        // Clear existing options (except the default "Choose a scenario...")
        while (scenarioSelect.options.length > 1) {
            scenarioSelect.remove(1);
        }

        scenarios.forEach(scenario => {
            const option = document.createElement('option');
            option.value = scenario.id;
            option.textContent = scenario.title;
            scenarioSelect.appendChild(option);
        });
    }

    // Function to fill content sections based on selected scenario
    function fillContent(scenarioId) {
        const selectedScenario = allScenarios.find(s => s.id === scenarioId);
        currentScenarioId = scenarioId; // <--- ADD THIS LINE!
        console.log("DEBUG: currentScenarioId set by fillContent to:", currentScenarioId); // <--- Make sure this line is also present for debugging

        if (selectedScenario) {
            // Update headings (optional, but good for clarity if they differ)
            document.querySelector('#initial-facts-section h2').textContent = selectedScenario.initialFacts.heading || "Initial Facts";
            document.querySelector('#key-actors-section h2').textContent = selectedScenario.keyActors.heading || "Key Actors";
            document.querySelector('#implications-section h2').textContent = selectedScenario.implications.heading || "Implications";
            document.querySelector('#justifications-section h2').textContent = selectedScenario.justifications.heading || "Justifications";

            // Update content using innerHTML to render the HTML strings from JSON
            factsContent.innerHTML = selectedScenario.initialFacts.content;
            actorsContent.innerHTML = selectedScenario.keyActors.content;
            implicationsContent.innerHTML = selectedScenario.implications.content;
            justificationsContent.innerHTML = selectedScenario.justifications.content;
        } else {
            // Reset content if no valid scenario is selected (e.g., "Choose a scenario...")
            factsContent.innerHTML = '<p>Select a scenario from the dropdown above to load content.</p>';
            actorsContent.innerHTML = '<p>Select a scenario from the dropdown above to load content.</p>';
            implicationsContent.innerHTML = '<p>Select a scenario from the dropdown above to load content.</p>';
            justificationsContent.innerHTML = '<p>Select a scenario from the dropdown above to load content.</p>';

            // Reset headings to default
            document.querySelector('#initial-facts-section h2').textContent = "Initial Facts";
            document.querySelector('#key-actors-section h2').textContent = "Key Actors";
            document.querySelector('#implications-section h2').textContent = "Implications";
            document.querySelector('#justifications-section h2').textContent = "Justifications";
        }
    }

    // Event listener for dropdown change
    scenarioSelect.addEventListener('change', (event) => {
        console.log("DEBUG: Scenario dropdown changed. New value:", event.target.value);
        fillContent(event.target.value);
        // Reset session ID when scenario changes, as new chat context is needed
        currentSessionId = null;
        // Optionally clear chat history if scenario changes
        chatBody.innerHTML = `<div class="message ai-message"><p>Hello!?</p></div>`;
    });

    // Load scenarios when the page loads
    loadScenarios();

    // Optionally, load the first scenario by default if available after loading
    // This is asynchronous, so call it after loadScenarios() is likely complete
    // You might want a small delay or use a more robust way to trigger this.
    // For now, let's keep it simple: the "Choose a scenario..." default will be there.
    // If you want the first scenario to load immediately, you can uncomment and adjust:
    // scenarioSelect.value = allScenarios.length > 0 ? allScenarios[0].id : '';
    // fillContent(scenarioSelect.value);

    // --- New Chat Functionality ---

    // Function to add a message to the chat body
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        const p = document.createElement('p');
        p.textContent = text;
        messageDiv.appendChild(p);
        chatBody.appendChild(messageDiv);

        // Scroll to the bottom of the chat
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    // Handle sending message
    async function sendMessage() {
        const userMessage = chatInput.value.trim();
        if (!userMessage) return; // Don't send empty messages
        if (userMessage) {
            addMessage(userMessage, 'user');
            chatInput.value = ''; // Clear input immediately

            if (!currentSessionId) {
                currentSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                console.log("New chat session ID generated:", currentSessionId);
            }

            // --- ADD THESE THREE LINES IMMEDIATELY BELOW THE ABOVE BLOCK ---
            console.log("DEBUG: Sending userMessage:", userMessage);
            console.log("DEBUG: Sending currentSessionId:", currentSessionId);
            console.log("DEBUG: Sending currentScenarioId:", currentScenarioId);
            // --- END ADDED LINES ---

            if (!currentScenarioId) {
                addMessage("Please select a scenario from the dropdown before starting the chat.", 'ai');
                console.error("No scenario selected for chat.");
                return; // IMPORTANT: This return should prevent the fetch call if scenarioId is missing
            }
            // Show a "typing" indicator or disable input temporarily
            // For now, we'll just wait for the response

            try {
                const response = await fetch('http://127.0.0.1:8000/chat', { // IMPORTANT: Use your FastAPI backend URL
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message: userMessage,
                        session_id: currentSessionId,
                        scenario_id: currentScenarioId 
                     })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }

                const data = await response.json();
                addMessage(data.response, 'ai'); // Display AI's response
            } catch (error) {
                console.error('Error sending message to backend:', error);
                addMessage("I'm sorry, I encountered an error. Please try again.", 'ai');
            }
        }
    }

    // Event listeners for chat buttons
    startChatBtn.addEventListener('click', () => {
        chatContainer.classList.add('open');
        startChatBtn.style.display = 'none';
        chatBody.innerHTML = `<div class="message ai-message"><p>Hello! How can I assist you with this scenario?</p></div>`;
        currentSessionId = null; // Reset session on starting a new chat
        currentScenarioId = scenarioSelect.value; // <<< ADD THIS LINE to explicitly set the current scenario ID
        console.log("DEBUG: Chat started. currentScenarioId set to:", currentScenarioId); // <<< ADD THIS FOR DEBUGGING
    });

    closeChatBtn.addEventListener('click', () => {
        chatContainer.classList.remove('open');
        startChatBtn.style.display = 'block';
        currentSessionId = null; // Clear session ID when chat closes
    });

    sendChatBtn.addEventListener('click', sendMessage);

    chatInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });
});
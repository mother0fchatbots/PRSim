document.addEventListener('DOMContentLoaded', () => {
    const scenarioSelect = document.getElementById('scenario-select');
    const factsContent = document.getElementById('facts-content');
    const actorsContent = document.getElementById('actors-content');
    const implicationsContent = document.getElementById('implications-content');
    const justificationsContent = document.getElementById('justifications-content');

    let allScenarios = []; // To store all loaded scenarios

    // Function to load scenarios from JSON
    async function loadScenarios() {
        try {
            const response = await fetch('scenarios.json');
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            allScenarios = await response.json();
            populateDropdown(allScenarios);
        } catch (error) {
            console.error('Error loading scenarios:', error);
            // Display an error message on the page if scenarios can't be loaded
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
        fillContent(event.target.value);
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
});
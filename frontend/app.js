// Frontend logic for the AI Interview Question Generator app

const jobTitleInput = document.getElementById("jobTitle");
const generateBtn   = document.getElementById("generateBtn");
const loadingEl     = document.getElementById("loading");
const spinnerText   = document.getElementById("spinnerText");
const resultsEl     = document.getElementById("results");
const questionsList = document.getElementById("questionsList");
const resultsRole   = document.getElementById("resultsRole");

// configure API base URL based on environment (local development vs deployed)

const API_BASE = (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1"
)
    ? "http://127.0.0.1:8001"
    : "https://interview-question-ai-ikvw.onrender.com";

const SPINNER_MESSAGES = [
    "Generating interview questions...",
    "Analyzing the role...",
    "Crafting thoughtful questions...",
    "Almost there...",
];


// Event listeners

generateBtn.addEventListener("click", generateQuestions);

// Support submitting with the Enter key
jobTitleInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") generateQuestions();
});

// Main function to handle the question generation process

async function generateQuestions() {
    const jobTitle = jobTitleInput.value.trim();

    clearResults();

    if (!jobTitle) {
        showError("Please enter a job title.");
        return;
    }

    setLoadingState(true);

    try {
        const response = await fetch(`${API_BASE}/api/questions/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job_title: jobTitle }),
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            showError(data.error || "Something went wrong. Please try again.");
            return;
        }

        if (!data.questions || typeof data.questions !== "string") {
            showError("Invalid response received from server.");
            return;
        }

        displayQuestions(data.questions, jobTitle);

    } catch {
        showError("Unable to connect to the server. Please try again.");

    } finally {
        setLoadingState(false);
    }
}

// Parses the raw questions text from the API, cleans it, and updates the UI to display the questions in a structured format.

function displayQuestions(questionsText, jobTitle) {

// The response is expected to be a string with questions numbered like "1. Question text".
    const cleaned = questionsText
        .replace(/\r/g, "")
        .replace(/\*\*/g, "")
        .trim();

// Split the cleaned text into individual questions based on the numbering pattern, trim whitespace, and filter out any empty entries.
    const questions = cleaned
        .split(/(?=^\d+\.)/m)
        .map((q) => q.trim())
        .filter(Boolean);

    if (questions.length === 0) {
        showError("Could not parse the generated questions. Please try again.");
        return;
    }

    resultsRole.textContent = jobTitle;

    questionsList.innerHTML = questions.map((question, index) => `
        <div class="question-item">
            <span class="question-number">${index + 1}</span>
            <p class="question-text">${sanitize(question.replace(/^\d+\.\s*/, ""))}</p>
        </div>
    `).join("");

    resultsEl.style.display = "block";
}

// Simple sanitization to prevent HTML injection in the displayed questions. It creates a temporary DOM element, sets its text content to the input, and then retrieves the sanitized HTML.
function sanitize(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    questionsList.innerHTML = `
        <div class="error-message">
            <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" stroke-width="2.5"
                stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <span>${message}</span>
        </div>
    `;
    resultsEl.style.display = "block";
}

function clearResults() {
    questionsList.innerHTML = "";
    resultsEl.style.display = "none";
    resultsRole.textContent = "";
}


let spinnerInterval = null;

// Manages the loading state of the UI by disabling the generate button and showing a spinner with rotating messages to indicate progress. When loading is complete, it clears the spinner and re-enables the button.
function setLoadingState(isLoading) {
    generateBtn.disabled = isLoading;

    if (isLoading) {
        let msgIndex = 0;
        spinnerText.textContent = SPINNER_MESSAGES[0];
        loadingEl.classList.add("active");

        spinnerInterval = setInterval(() => {
            msgIndex = (msgIndex + 1) % SPINNER_MESSAGES.length;
            spinnerText.textContent = SPINNER_MESSAGES[msgIndex];
        }, 1800);

    } else {
        clearInterval(spinnerInterval);
        loadingEl.classList.remove("active");
        spinnerText.textContent = SPINNER_MESSAGES[0];
    }
}
// Function to update timestamp
function updateTimestamp() {
    const now = new Date();
    const timeString = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    document.getElementById('timestamp').textContent = timeString;
}

// Function to simulate loading animation
function showLoading() {
    document.getElementById('loadingAnimation').style.display = 'flex';
    document.getElementById('answerText').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loadingAnimation').style.display = 'none';
    document.getElementById('answerText').style.display = 'block';
}

// Function to update question and answer
function updateResponse(question, answer) {
    document.getElementById('questionText').textContent = question;
    document.getElementById('answerText').textContent = answer;
    updateTimestamp();
}

// Function to copy response to clipboard
function copyToClipboard() {
    const question = document.getElementById('questionText').textContent;
    const answer = document.getElementById('answerText').textContent;
    const text = `Question: ${question}\n\nAnswer: ${answer}`;

    navigator.clipboard.writeText(text).then(() => {
        const copyBtn = document.querySelector('.action-btn');
        copyBtn.classList.add('copy-success');
        setTimeout(() => {
            copyBtn.classList.remove('copy-success');
        }, 300);
    });
}

// Function to share response
function shareResponse() {
    const question = document.getElementById('questionText').textContent;
    const answer = document.getElementById('answerText').textContent;

    if (navigator.share) {
        navigator.share({
            title: 'Basketball Oracle AI Response',
            text: `Question: ${question}\n\nAnswer: ${answer}`
        });
    } else {
        copyToClipboard();
    }
}

// Initialize timestamp
updateTimestamp();

// Example of how to use the functions (you can remove this in production)
// Simulate loading for demonstration
setTimeout(() => {
    showLoading();
    setTimeout(() => {
        hideLoading();
    }, 2000);
}, 3000);

document.addEventListener("DOMContentLoaded", function () {
    const outputDiv = document.getElementById("answerText");
    const loadingDiv = document.getElementById("loadingAnimation");
    loadingDiv.style.display = "block";

    fetch("/stream_response").then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        function readStream() {
            reader.read().then(({ done, value }) => {
                if (done) {
                    loadingDiv.style.display = "none";
                    return;
                }
                const chunk = decoder.decode(value);
                outputDiv.textContent += chunk;
                readStream();
            });
        }

        readStream();
    });
});

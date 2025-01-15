// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Function to handle the prep form submission
function handlePrepSubmission(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitButton = form.querySelector('input[type="submit"]');
    const statusDiv = document.getElementById('ai-status');
    const statusMessage = statusDiv.querySelector('.status-message');
    const spinner = statusDiv.querySelector('.spinner-border');
    
    // Get the project name from the hidden input
    const projectName = form.querySelector('input[name="project_name"]').value;
    
    // Disable submit button and show spinner
    submitButton.disabled = true;
    spinner.classList.remove('d-none');
    statusMessage.textContent = 'Processing your data...';
    
    // Send the form data
    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            project_name: projectName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.task_id) {
            // Start polling for task status
            pollTaskStatus(data.task_id, statusMessage, spinner, submitButton);
        } else {
            throw new Error('No task ID received');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        statusMessage.textContent = 'An error occurred while starting the task';
        spinner.classList.add('d-none');
        submitButton.disabled = false;
    });
}

// Function to poll task status
function pollTaskStatus(taskId, statusMessage, spinner, submitButton) {
    const pollInterval = setInterval(() => {
        fetch(`/projects/task-status/${taskId}/`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'done') {
                clearInterval(pollInterval);
                statusMessage.textContent = 'Processing complete!';
                spinner.classList.add('d-none');
                submitButton.disabled = false;
                
                // Optional: Reload the page or update specific elements
                // window.location.reload();
            } else if (data.status === 'failed') {
                clearInterval(pollInterval);
                statusMessage.textContent = `Error: ${data.error}`;
                spinner.classList.add('d-none');
                submitButton.disabled = false;
            } else if (data.status === 'pending') {
                statusMessage.textContent = 'Processing your data...';
            }
        })
        .catch(error => {
            clearInterval(pollInterval);
            console.error('Error:', error);
            statusMessage.textContent = 'Error checking task status';
            spinner.classList.add('d-none');
            submitButton.disabled = false;
        });
    }, 2000); // Poll every 2 seconds
}

// Add event listener when document is loaded
document.addEventListener('DOMContentLoaded', () => {
    const prepForm = document.getElementById('prep-form');
    if (prepForm) {
        prepForm.addEventListener('submit', handlePrepSubmission);
    }
});
document.addEventListener('DOMContentLoaded', function () {
    // Form validation
    const form = document.querySelector('form');
    form.addEventListener('submit', function (event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        form.classList.add('was-validated');
    });

    // File input validation
    const fileInput = document.getElementById('id_input_dataframe');
    fileInput.addEventListener('change', function (e) {
        const file = e.target.files[0];
        if (file) {
            if (!file.name.toLowerCase().endsWith('.csv')) {
                fileInput.value = '';
                const alert = document.createElement('div');
                alert.className = 'alert alert-danger mt-2';
                alert.textContent = 'Please select a CSV file.';
                fileInput.parentElement.appendChild(alert);
                setTimeout(() => alert.remove(), 5000);
            }
        }
    });
});
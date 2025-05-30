document.addEventListener('DOMContentLoaded', function() {
    const uploadBox = document.getElementById('uploadBox');
    const fileInput = document.getElementById('fileInput');
    const resultBox = document.getElementById('resultBox');
    const previewImage = document.getElementById('previewImage');
    const resultText = document.getElementById('resultText');
    const confidenceValue = document.getElementById('confidenceValue');
    const resetBtn = document.getElementById('resetBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultBadge = document.getElementById('resultBadge');

    uploadBox.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Show preview
        const reader = new FileReader();
        reader.onload = (event) => {
            previewImage.src = event.target.result;
            uploadBox.classList.add('hidden');
            loadingSpinner.classList.remove('hidden');
        };
        reader.readAsDataURL(file);

        // Send to API
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/predict/', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            loadingSpinner.classList.add('hidden');

            if (data.status === 'success') {
                resultText.textContent = data.prediction === 'parasitized'
                    ? 'Parasitized (Malaria Detected)'
                    : 'Uninfected (No Malaria)';

                confidenceValue.textContent = `${data.confidence}%`;

                // Set color based on result
                if (data.prediction === 'parasitized') {
                    resultBadge.style.background = 'rgba(247, 37, 133, 0.1)';
                    resultBadge.style.color = 'var(--danger)';
                } else {
                    resultBadge.style.background = 'rgba(76, 201, 240, 0.1)';
                    resultBadge.style.color = 'var(--success)';
                }

                resultBox.classList.remove('hidden');
            } else {
                alert(`Error: ${data.message}`);
                resetUpload();
            }
        } catch (error) {
            loadingSpinner.classList.add('hidden');
            alert(`Error: ${error.message}`);
            resetUpload();
        }
    });

    resetBtn.addEventListener('click', resetUpload);

    function resetUpload() {
        fileInput.value = '';
        uploadBox.classList.remove('hidden');
        resultBox.classList.add('hidden');
        loadingSpinner.classList.add('hidden');
    }

    // Drag and drop functionality
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.style.background = 'rgba(67, 97, 238, 0.1)';
    });

    uploadBox.addEventListener('dragleave', () => {
        uploadBox.style.background = '';
    });

    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.style.background = '';
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            const event = new Event('change');
            fileInput.dispatchEvent(event);
        }
    });
});
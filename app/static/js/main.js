const form = document.getElementById('redirect-rules-form');
const logsDiv = document.getElementById('logs');
const progressBar = document.getElementById('progress-bar');  // Lấy thanh tiến trình

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Đặt tiến trình ban đầu là 0
    updateProgress(0);

    logsDiv.textContent = 'Processing...';

    const formData = new FormData(form);
    const response = await fetch('', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    
    // Cập nhật thanh tiến trình và logs
    logsDiv.textContent = result.logs.join('\n');
    
    // Đặt tiến trình là 100% khi hoàn thành
    updateProgress(100);
});

// Hàm cập nhật thanh tiến trình
function updateProgress(percentage) {
    if (progressBar) {
        progressBar.style.width = percentage + '%';
        progressBar.setAttribute('aria-valuenow', percentage);
        progressBar.textContent = percentage + '%';
    }
}

function clearFields() {
    document.getElementById('domains').value = '';
    document.getElementById('target_domain').value = '';
    document.getElementById('path').value = '';
    document.getElementById('status_code').value = '301';
    logsDiv.textContent = '';

    // Đặt lại thanh tiến trình về 0%
    updateProgress(0);
}

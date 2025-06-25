// Grab references to DOM elements
const input = document.getElementById('pdf-input');
const fileList = document.getElementById('file-list');
const processBtn = document.getElementById('process-btn');
const clearBtn = document.getElementById('clear-btn');
const statusP = document.getElementById('status');

let selectedFiles = [];

// When files are selected, update list and enable the Process button
input.addEventListener('change', () => {
  selectedFiles = Array.from(input.files);
  fileList.innerHTML = '';
  selectedFiles.forEach(file => {
    const li = document.createElement('li');
    li.textContent = file.name;
    fileList.appendChild(li);
  });
  processBtn.disabled = selectedFiles.length === 0;
});

// When “Process chosen PDFs” is clicked, send files to the server
processBtn.addEventListener('click', async () => {
  processBtn.disabled = true;
  statusP.textContent = 'Processing…';

  const form = new FormData();
  selectedFiles.forEach(file => form.append('pdfs', file));

  try {
    const response = await fetch('/process', {
      method: 'POST',
      body: form
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || 'Server error');
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'processed_csvs.zip';
    a.click();

    statusP.textContent = 'Files saved! 🎉';
    clearBtn.hidden = false;
  } catch (err) {
    statusP.textContent = 'Error: ' + err.message;
    processBtn.disabled = false;
  }
});

// When “Refresh / Start Again” is clicked, reset the form
clearBtn.addEventListener('click', () => {
  input.value = '';
  fileList.innerHTML = '';
  statusP.textContent = '';
  clearBtn.hidden = true;
  processBtn.disabled = true;
});

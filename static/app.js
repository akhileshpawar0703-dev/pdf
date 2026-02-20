const statusEl = document.getElementById('status');
const modeButtons = document.querySelectorAll('.mode-btn');
const pdfWorkspace = document.getElementById('pdf-workspace');
const imageWorkspace = document.getElementById('image-workspace');

const previewLabel = document.getElementById('preview-label');
const imagePreview = document.getElementById('image-preview');
const pdfPreview = document.getElementById('pdf-preview');
const multiPreview = document.getElementById('multi-preview');
const previewPlaceholder = document.getElementById('preview-placeholder');
const clearPreviewBtn = document.getElementById('clear-preview');

const accentStyle = document.getElementById('accent-style');
const rememberWorkspace = document.getElementById('remember-workspace');

function setMode(mode, save = true) {
  const pdfMode = mode === 'pdf';
  pdfWorkspace.classList.toggle('hidden', !pdfMode);
  imageWorkspace.classList.toggle('hidden', pdfMode);

  modeButtons.forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.mode === mode);
  });

  resetAccordionForMode(mode);

  if (save && rememberWorkspace.checked) {
    localStorage.setItem('studiopdf.mode', mode);
  }
}

function clearPreview() {
  imagePreview.hidden = true;
  pdfPreview.hidden = true;
  imagePreview.removeAttribute('src');
  pdfPreview.removeAttribute('src');
  multiPreview.innerHTML = '';
  previewLabel.textContent = 'Select a file from any tool to preview it here.';
  if (previewPlaceholder) previewPlaceholder.hidden = false;
}

function updatePreview(fileInput) {
  const files = Array.from(fileInput.files || []);
  clearPreview();

  if (!files.length) {
    return;
  }

  previewLabel.textContent = `Selected: ${files.map((f) => f.name).join(', ')}`;
  if (previewPlaceholder) previewPlaceholder.hidden = true;

  if (files.length > 1) {
    files.forEach((f) => {
      const li = document.createElement('li');
      li.textContent = `${f.name} (${Math.round(f.size / 1024)} KB)`;
      multiPreview.appendChild(li);
    });
    return;
  }

  const [file] = files;
  const url = URL.createObjectURL(file);

  if (file.type.startsWith('image/')) {
    imagePreview.src = url;
    imagePreview.hidden = false;
  } else if (file.type === 'application/pdf') {
    pdfPreview.src = url;
    pdfPreview.hidden = false;
  } else {
    const li = document.createElement('li');
    li.textContent = file.name;
    multiPreview.appendChild(li);
  }
}


function initAccordion(scope) {
  const items = scope.querySelectorAll('.tool-item');
  items.forEach((item) => {
    if (!item.dataset.bound) {
      item.addEventListener('toggle', () => {
        if (!item.open) return;
        items.forEach((other) => {
          if (other !== item) other.open = false;
        });
      });
      item.dataset.bound = '1';
    }
  });
}

function resetAccordionForMode(mode) {
  const activeScope = mode === 'pdf' ? pdfWorkspace : imageWorkspace;
  const items = activeScope.querySelectorAll('.tool-item');
  items.forEach((item, idx) => {
    item.open = idx === 0;
  });
}

function applyAccent(theme) {
  document.body.classList.remove('theme-violet', 'theme-emerald');
  if (theme === 'violet') document.body.classList.add('theme-violet');
  if (theme === 'emerald') document.body.classList.add('theme-emerald');
  localStorage.setItem('studiopdf.accent', theme);
}

async function submitForm(form) {
  const endpoint = form.dataset.endpoint;
  const formData = new FormData(form);
  statusEl.textContent = 'Processing...';

  try {
    const res = await fetch(endpoint, { method: 'POST', body: formData });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Request failed');
    }

    const blob = await res.blob();
    const dispo = res.headers.get('Content-Disposition') || '';
    const match = dispo.match(/filename="?([^";]+)"?/);
    const filename = match ? match[1] : 'download.bin';

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    statusEl.textContent = 'Done. Download started.';
  } catch (e) {
    statusEl.textContent = `Error: ${e.message}`;
  }
}

modeButtons.forEach((btn) => {
  btn.addEventListener('click', () => setMode(btn.dataset.mode));
});

document.querySelectorAll('input[type="file"]').forEach((input) => {
  input.addEventListener('change', () => updatePreview(input));
});

document.querySelectorAll('form[data-endpoint]').forEach((form) => {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    submitForm(form);
  });
});

clearPreviewBtn.addEventListener('click', clearPreview);
accentStyle.addEventListener('change', () => applyAccent(accentStyle.value));
rememberWorkspace.addEventListener('change', () => {
  if (!rememberWorkspace.checked) localStorage.removeItem('studiopdf.mode');
});

initAccordion(pdfWorkspace);
initAccordion(imageWorkspace);

const savedTheme = localStorage.getItem('studiopdf.accent') || 'blue';
accentStyle.value = savedTheme;
applyAccent(savedTheme);

const savedMode = localStorage.getItem('studiopdf.mode');
if (savedMode === 'pdf' || savedMode === 'image') {
  setMode(savedMode, false);
}

if (!(savedMode === 'pdf' || savedMode === 'image')) {
  resetAccordionForMode('pdf');
}

const statusEl = document.getElementById('status');
const panelButtons = document.querySelectorAll('.panel-btn');
const settingsPanel = document.getElementById('settings-panel');
const pdfWorkspace = document.getElementById('pdf-workspace');
const imageWorkspace = document.getElementById('image-workspace');
const panels = [settingsPanel, pdfWorkspace, imageWorkspace].filter(Boolean);

const previewLabel = document.getElementById('preview-label');
const imagePreview = document.getElementById('image-preview');
const pdfPreview = document.getElementById('pdf-preview');
const multiPreview = document.getElementById('multi-preview');
const previewPlaceholder = document.getElementById('preview-placeholder');
const clearPreviewBtn = document.getElementById('clear-preview');

const accentStyle = document.getElementById('accent-style');
const rememberWorkspace = document.getElementById('remember-workspace');
const whiteThemeBtn = document.getElementById('white-theme-btn');
const darkModeBtn = document.getElementById('dark-mode-btn');
const appearanceMode = document.getElementById('appearance-mode');
const activityLog = document.getElementById('activity-log');
const clearActivityBtn = document.getElementById('clear-activity');
const toolSearch = document.getElementById('tool-search');
const toolbarActionButtons = document.querySelectorAll('.toolbar-action');

function setActivePanel(panelId, save = true) {
  const target = document.getElementById(panelId);
  if (!target) return;

  const wasHidden = target.hidden;
  panels.forEach((panel) => { panel.hidden = true; });
  panelButtons.forEach((btn) => btn.classList.remove('active'));

  if (wasHidden) {
    target.hidden = false;
    const activeBtn = document.querySelector(`.panel-btn[data-panel="${panelId}"]`);
    if (activeBtn) activeBtn.classList.add('active');

    if (panelId === 'pdf-workspace') resetAccordionForWorkspace(pdfWorkspace);
    if (panelId === 'image-workspace') resetAccordionForWorkspace(imageWorkspace);

    if (save && rememberWorkspace.checked) {
      localStorage.setItem('studiopdf.panel', panelId);
    }
  } else if (save && rememberWorkspace.checked) {
    localStorage.removeItem('studiopdf.panel');
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
  if (!files.length) return;

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

function resetAccordionForWorkspace(scope) {
  const items = scope.querySelectorAll('.tool-item');
  items.forEach((item, idx) => {
    item.open = idx === 0;
  });
}


function filterTools(query) {
  const q = (query || '').trim().toLowerCase();
  [pdfWorkspace, imageWorkspace].forEach((scope) => {
    const items = scope.querySelectorAll('.tool-item');
    items.forEach((item) => {
      const label = item.querySelector('summary')?.textContent?.toLowerCase() || '';
      const match = !q || label.includes(q);
      item.classList.toggle('hidden-by-search', !match);
    });
  });
}

function setToolbarOpenState(workspaceId, expand) {
  const scope = document.getElementById(workspaceId);
  if (!scope) return;
  scope.querySelectorAll('.tool-item').forEach((item) => {
    if (item.classList.contains('hidden-by-search')) return;
    item.open = expand;
  });
}

function applyAppearance(mode) {
  document.body.classList.remove('theme-dark');
  let resolved = mode;
  if (mode === 'system') {
    resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  if (resolved === 'dark') {
    document.body.classList.add('theme-dark');
  }
  localStorage.setItem('studiopdf.appearance', mode);
}

function enableDarkTheme() {
  if (appearanceMode) appearanceMode.value = 'dark';
  applyAppearance('dark');
}

function applyAccent(theme) {
  document.body.classList.remove('theme-violet', 'theme-emerald', 'theme-white');
  if (theme === 'violet') document.body.classList.add('theme-violet');
  if (theme === 'emerald') document.body.classList.add('theme-emerald');
  if (theme === 'white') document.body.classList.add('theme-white');
  localStorage.setItem('studiopdf.accent', theme);
}

function enableWhiteTheme() {
  accentStyle.value = 'white';
  applyAccent('white');
}


function addActivity(message, kind = 'info') {
  if (!activityLog) return;
  const empty = activityLog.querySelector('.muted');
  if (empty) empty.remove();

  const li = document.createElement('li');
  li.className = `activity-item ${kind}`;
  const stamp = new Date().toLocaleTimeString();
  li.textContent = `[${stamp}] ${message}`;
  activityLog.prepend(li);

  const maxItems = 8;
  while (activityLog.children.length > maxItems) {
    activityLog.removeChild(activityLog.lastElementChild);
  }
}

function clearActivityLog() {
  if (!activityLog) return;
  activityLog.innerHTML = '<li class="muted">No actions yet.</li>';
}

function formatBytes(n) {
  const size = Number(n || 0);
  if (!size) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  let v = size;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i += 1;
  }
  return `${v.toFixed(v >= 100 || i === 0 ? 0 : 1)} ${units[i]}`;
}

function updateFileSizeHint(fileInput) {
  const form = fileInput.closest('form');
  if (!form) return;
  const hint = form.querySelector(`.file-size-hint[data-for="${fileInput.name}"]`);
  if (!hint) return;
  const files = Array.from(fileInput.files || []);
  if (!files.length) {
    hint.textContent = 'Current size: -';
    return;
  }
  const total = files.reduce((acc, f) => acc + f.size, 0);
  hint.textContent = `Current size: ${formatBytes(total)}`;
}

async function submitForm(form) {
  const endpoint = form.dataset.endpoint;
  const formData = new FormData(form);
  statusEl.textContent = 'Processing...';
  addActivity(`Started ${endpoint}`, 'info');

  try {
    const res = await fetch(endpoint, { method: 'POST', body: formData });
    if (!res.ok) {
      let message = 'Request failed';
      const ctype = res.headers.get('content-type') || '';
      if (ctype.includes('application/json')) {
        const err = await res.json();
        message = err.error || message;
      } else {
        const txt = await res.text();
        if (txt) message = txt;
      }
      throw new Error(message);
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
    const inSize = res.headers.get('X-Original-Size');
    const outSize = res.headers.get('X-Output-Size');
    if (inSize && outSize) {
      statusEl.textContent = `Done. ${formatBytes(inSize)} → ${formatBytes(outSize)}. Download started.`;
      addActivity(`Completed ${endpoint} → ${filename} (${formatBytes(inSize)} → ${formatBytes(outSize)})`, 'success');
    } else {
      statusEl.textContent = 'Done. Download started.';
      addActivity(`Completed ${endpoint} → ${filename}`, 'success');
    }
  } catch (e) {
    statusEl.textContent = `Error: ${e.message}`;
    addActivity(`Failed ${endpoint}: ${e.message}`, 'error');
  }
}

panelButtons.forEach((btn) => {
  btn.addEventListener('click', () => setActivePanel(btn.dataset.panel));
});

document.querySelectorAll('input[type="file"]').forEach((input) => {
  input.addEventListener('change', () => { updatePreview(input); updateFileSizeHint(input); });
});

document.querySelectorAll('form[data-endpoint]').forEach((form) => {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    submitForm(form);
  });
});

clearPreviewBtn.addEventListener('click', clearPreview);
accentStyle.addEventListener('change', () => applyAccent(accentStyle.value));
if (whiteThemeBtn) whiteThemeBtn.addEventListener('click', enableWhiteTheme);
if (darkModeBtn) darkModeBtn.addEventListener('click', enableDarkTheme);
if (appearanceMode) appearanceMode.addEventListener('change', () => applyAppearance(appearanceMode.value));
if (clearActivityBtn) clearActivityBtn.addEventListener('click', clearActivityLog);
if (toolSearch) toolSearch.addEventListener('input', () => filterTools(toolSearch.value));
toolbarActionButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    const expand = btn.dataset.action === 'expand';
    setToolbarOpenState(btn.dataset.target, expand);
  });
});

rememberWorkspace.addEventListener('change', () => {
  if (!rememberWorkspace.checked) localStorage.removeItem('studiopdf.panel');
});

initAccordion(pdfWorkspace);
initAccordion(imageWorkspace);

const savedAppearance = localStorage.getItem('studiopdf.appearance') || 'system';
if (appearanceMode) appearanceMode.value = savedAppearance;
applyAppearance(savedAppearance);

const savedTheme = localStorage.getItem('studiopdf.accent') || 'white';
accentStyle.value = savedTheme;
applyAccent(savedTheme);

const savedPanel = localStorage.getItem('studiopdf.panel');
if (savedPanel && document.getElementById(savedPanel)) {
  setActivePanel(savedPanel, false);
} else {
  setActivePanel('pdf-workspace', false);
}

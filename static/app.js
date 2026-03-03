import * as pdfjsLib from "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.min.mjs";

pdfjsLib.GlobalWorkerOptions.workerSrc =
  "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.worker.min.mjs";

const fileInput = document.getElementById("file-input");
const fileNameLabel = document.getElementById("file-name");
const canvas = document.getElementById("pdf-canvas");
const ctx = canvas.getContext("2d");
const totalPagesLabel = document.getElementById("total-pages");
const pageNumberInput = document.getElementById("page-number");
const prevPageButton = document.getElementById("prev-page");
const nextPageButton = document.getElementById("next-page");
const zoomLevelSelect = document.getElementById("zoom-level");
const zoomInButton = document.getElementById("zoom-in");
const zoomOutButton = document.getElementById("zoom-out");
const fitWidthButton = document.getElementById("fit-width");
const rotateButton = document.getElementById("rotate");
const emptyState = document.getElementById("empty-state");
const thumbnailPanel = document.getElementById("thumbnail-panel");
const viewerPanel = document.getElementById("viewer-panel");

const state = {
  pdf: null,
  pageNum: 1,
  scale: 1,
  rotation: 0,
  rendering: false,
  pendingPage: null,
};

const queueRenderPage = (num) => {
  if (state.rendering) {
    state.pendingPage = num;
    return;
  }
  renderPage(num);
};

const updateActiveThumbnail = () => {
  [...thumbnailPanel.querySelectorAll(".thumbnail")].forEach((thumb, index) => {
    thumb.classList.toggle("active", index + 1 === state.pageNum);
  });
};

const renderPage = async (num) => {
  if (!state.pdf) return;

  state.rendering = true;
  const page = await state.pdf.getPage(num);
  const viewport = page.getViewport({ scale: state.scale, rotation: state.rotation });

  canvas.width = viewport.width;
  canvas.height = viewport.height;

  await page.render({ canvasContext: ctx, viewport }).promise;

  state.rendering = false;
  if (state.pendingPage !== null) {
    const pending = state.pendingPage;
    state.pendingPage = null;
    renderPage(pending);
  }

  pageNumberInput.value = state.pageNum;
  updateActiveThumbnail();
};

const renderThumbnails = async () => {
  thumbnailPanel.innerHTML = "";

  for (let index = 1; index <= state.pdf.numPages; index += 1) {
    const page = await state.pdf.getPage(index);
    const viewport = page.getViewport({ scale: 0.2 });
    const thumbCanvas = document.createElement("canvas");
    thumbCanvas.width = viewport.width;
    thumbCanvas.height = viewport.height;
    thumbCanvas.className = "thumbnail";

    await page.render({ canvasContext: thumbCanvas.getContext("2d"), viewport }).promise;

    thumbCanvas.addEventListener("click", () => {
      state.pageNum = index;
      queueRenderPage(index);
    });

    thumbnailPanel.append(thumbCanvas);
  }

  updateActiveThumbnail();
};

const uploadAndLoadPdf = async (file) => {
  const formData = new FormData();
  formData.append("pdf", file);

  const response = await fetch("/upload", { method: "POST", body: formData });
  if (!response.ok) {
    throw new Error("Upload failed.");
  }

  const payload = await response.json();
  fileNameLabel.textContent = payload.name;

  const loadingTask = pdfjsLib.getDocument(payload.url);
  state.pdf = await loadingTask.promise;
  state.pageNum = 1;
  state.scale = Number(zoomLevelSelect.value);
  state.rotation = 0;

  totalPagesLabel.textContent = state.pdf.numPages;
  pageNumberInput.max = state.pdf.numPages;
  canvas.style.display = "block";
  emptyState.style.display = "none";

  queueRenderPage(state.pageNum);
  renderThumbnails();
};

fileInput.addEventListener("change", async (event) => {
  const [file] = event.target.files;
  if (!file) return;

  try {
    await uploadAndLoadPdf(file);
  } catch (error) {
    fileNameLabel.textContent = "Failed to load PDF";
  }
});

prevPageButton.addEventListener("click", () => {
  if (!state.pdf || state.pageNum <= 1) return;
  state.pageNum -= 1;
  queueRenderPage(state.pageNum);
});

nextPageButton.addEventListener("click", () => {
  if (!state.pdf || state.pageNum >= state.pdf.numPages) return;
  state.pageNum += 1;
  queueRenderPage(state.pageNum);
});

pageNumberInput.addEventListener("change", () => {
  if (!state.pdf) return;
  const desiredPage = Number(pageNumberInput.value);
  if (!desiredPage || desiredPage < 1 || desiredPage > state.pdf.numPages) {
    pageNumberInput.value = state.pageNum;
    return;
  }
  state.pageNum = desiredPage;
  queueRenderPage(desiredPage);
});

zoomLevelSelect.addEventListener("change", () => {
  state.scale = Number(zoomLevelSelect.value);
  queueRenderPage(state.pageNum);
});

zoomInButton.addEventListener("click", () => {
  state.scale = Math.min(3, Number((state.scale + 0.1).toFixed(2)));
  queueRenderPage(state.pageNum);
});

zoomOutButton.addEventListener("click", () => {
  state.scale = Math.max(0.25, Number((state.scale - 0.1).toFixed(2)));
  queueRenderPage(state.pageNum);
});

fitWidthButton.addEventListener("click", async () => {
  if (!state.pdf) return;
  const page = await state.pdf.getPage(state.pageNum);
  const viewport = page.getViewport({ scale: 1 });
  state.scale = (viewerPanel.clientWidth - 48) / viewport.width;
  queueRenderPage(state.pageNum);
});

rotateButton.addEventListener("click", () => {
  state.rotation = (state.rotation + 90) % 360;
  queueRenderPage(state.pageNum);
});

const fileInput = document.getElementById("fileInput");
const dropzone = document.getElementById("dropzone");
const uploadBtn = document.getElementById("uploadBtn");
const uploadStatus = document.getElementById("uploadStatus");

const questionInput = document.getElementById("questionInput");
const askBtn = document.getElementById("askBtn");
const loadingEl = document.getElementById("loading");
const answerEl = document.getElementById("answer");
const sourcesEl = document.getElementById("sources");

let selectedFile = null;

dropzone.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", (e) => {
  selectedFile = e.target.files[0] || null;
  if (selectedFile) {
    uploadStatus.textContent = `Selected: ${selectedFile.name}`;
  }
});

["dragenter","dragover"].forEach(evt =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.add("dragover");
  })
);

["dragleave","drop"].forEach(evt =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove("dragover");
  })
);

dropzone.addEventListener("drop", (e) => {
  const dt = e.dataTransfer;
  const files = dt.files;
  if (files && files[0]) {
    selectedFile = files[0];
    fileInput.files = files; // sync with input
    uploadStatus.textContent = `Selected: ${selectedFile.name}`;
  }
});

uploadBtn.addEventListener("click", async () => {
  if (!selectedFile) {
    uploadStatus.textContent = "Please choose a file first.";
    return;
  }
  const form = new FormData();
  form.append("file", selectedFile);
  uploadStatus.textContent = "Uploading & indexing…";

  try {
    const res = await fetch("/api/upload", {
      method: "POST",
      body: form
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload failed");

    uploadStatus.textContent = `✅ ${data.message}. File: ${data.file} | Chunks: ${data.chunks}`;
  } catch (err) {
    uploadStatus.textContent = `❌ ${err.message}`;
  }
});

askBtn.addEventListener("click", async () => {
  const q = (questionInput.value || "").trim();
  if (!q) return;

  loadingEl.classList.remove("hidden");
  answerEl.textContent = "";
  sourcesEl.innerHTML = "";

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Ask failed");

    answerEl.textContent = data.answer || "(No answer)";

    const sources = data.sources || [];
    sources.forEach(src => {
      const div = document.createElement("div");
      div.className = "source";
      const page = (src.page !== undefined && src.page !== null) ? ` | page ${src.page}` : "";
      const fileName = src?.metadata?.source || src?.metadata?.file || "uploaded document";
      div.innerHTML = `
        <div class="meta"><strong>Source ${src.id}</strong> — ${fileName}${page}</div>
        <div class="snippet">${escapeHtml(src.snippet || "")}</div>
      `;
      sourcesEl.appendChild(div);
    });

  } catch (err) {
    answerEl.textContent = `❌ ${err.message}`;
  } finally {
    loadingEl.classList.add("hidden");
  }
});

function escapeHtml(str){
  return str.replace(/[&<>"']/g, (m) => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[m]));
}

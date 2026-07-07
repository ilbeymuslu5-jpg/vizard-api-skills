const API = "/api/v1/project";

const tabs = document.querySelectorAll(".tab");
const tabContents = document.querySelectorAll(".tab-content");
tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const target = tab.dataset.tab;
    tabContents.forEach((c) => c.classList.toggle("hidden", c.dataset.tabContent !== target));
  });
});

const form = document.getElementById("project-form");
const submitBtn = document.getElementById("submit-btn");
const progressPanel = document.getElementById("progress-panel");
const resultsPanel = document.getElementById("results-panel");
const progressFill = document.getElementById("progress-fill");
const progressLabel = document.getElementById("progress-label");
const clipGrid = document.getElementById("clip-grid");

let pollTimer = null;

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  submitBtn.disabled = true;
  resultsPanel.classList.add("hidden");
  clipGrid.innerHTML = "";

  const activeTab = document.querySelector(".tab.active").dataset.tab;
  const fd = new FormData();

  if (activeTab === "upload") {
    const file = document.getElementById("file-input").files[0];
    if (!file) {
      alert("Choose a video file first.");
      submitBtn.disabled = false;
      return;
    }
    fd.append("file", file);
  } else {
    const url = document.getElementById("url-input").value.trim();
    if (!url) {
      alert("Enter a video URL first.");
      submitBtn.disabled = false;
      return;
    }
    fd.append("videoUrl", url);
    fd.append("videoType", document.getElementById("video-type").value);
  }

  fd.append("lang", document.getElementById("lang").value);
  fd.append("preferLength", document.getElementById("prefer-length").value);
  fd.append("ratioOfClip", document.getElementById("ratio").value);
  fd.append("maxClipCount", document.getElementById("max-clips").value);
  fd.append("subtitleSwitch", document.getElementById("subtitles").checked ? "1" : "0");
  fd.append("headlineSwitch", document.getElementById("headline").checked ? "1" : "0");
  fd.append("highlightSwitch", document.getElementById("highlight").checked ? "1" : "0");
  fd.append("removeSilenceSwitch", document.getElementById("remove-silence").checked ? "1" : "0");
  fd.append("captionFont", document.getElementById("caption-font").value);

  try {
    const resp = await fetch(`${API}/create`, { method: "POST", body: fd });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "Request failed");

    progressPanel.classList.remove("hidden");
    pollProject(data.projectId);
  } catch (err) {
    alert(`Failed to submit: ${err.message}`);
    submitBtn.disabled = false;
  }
});

function pollProject(projectId) {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    const resp = await fetch(`${API}/query/${projectId}`);
    const data = await resp.json();
    progressFill.style.width = `${data.progress || 0}%`;
    progressLabel.textContent = data.message || data.status;

    if (data.status === "completed") {
      clearInterval(pollTimer);
      submitBtn.disabled = false;
      renderClips(data.videos || []);
    } else if (data.status === "failed") {
      clearInterval(pollTimer);
      submitBtn.disabled = false;
      progressLabel.textContent = `Error: ${data.message}`;
    }
  }, 2000);
}

function renderClips(videos) {
  resultsPanel.classList.remove("hidden");
  clipGrid.innerHTML = "";
  videos
    .slice()
    .sort((a, b) => parseFloat(b.viralScore) - parseFloat(a.viralScore))
    .forEach((v) => {
      const card = document.createElement("div");
      card.className = "clip-card";
      card.innerHTML = `
        <video src="${v.videoUrl}" controls preload="metadata" poster="${v.thumbnailUrl}"></video>
        <div class="clip-body">
          <span class="clip-score">Viral score ${v.viralScore}/10</span>
          <div class="clip-title">${escapeHtml(v.title)}</div>
          <div class="clip-reason">${escapeHtml(v.viralReason)}</div>
          <div class="clip-actions">
            <a href="${v.videoUrl}" download>Download</a>
            <button data-video-id="${v.videoId}" class="caption-btn">Caption</button>
          </div>
        </div>`;
      clipGrid.appendChild(card);
    });

  document.querySelectorAll(".caption-btn").forEach((btn) => {
    btn.addEventListener("click", () => openCaptionModal(btn.dataset.videoId));
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

const captionModal = document.getElementById("caption-modal");
const captionOutput = document.getElementById("caption-output");
let currentVideoId = null;

function openCaptionModal(videoId) {
  currentVideoId = videoId;
  captionOutput.value = "";
  captionModal.classList.remove("hidden");
}

document.getElementById("caption-close").addEventListener("click", () => {
  captionModal.classList.add("hidden");
});

document.getElementById("caption-generate").addEventListener("click", async () => {
  const platform = document.getElementById("caption-platform").value;
  const tone = document.getElementById("caption-tone").value;
  captionOutput.value = "Generating...";
  try {
    const resp = await fetch(`${API}/ai-social`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        finalVideoId: currentVideoId,
        aiSocialPlatform: parseInt(platform, 10),
        tone: parseInt(tone, 10),
        voice: 0,
      }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "Failed");
    captionOutput.value = data.aiSocialContent;
  } catch (err) {
    captionOutput.value = `Error: ${err.message}`;
  }
});

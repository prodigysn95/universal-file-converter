const modeSelect = document.getElementById("modeSelect");
const formatSelect = document.getElementById("formatSelect");
const progressBar = document.getElementById("progressBar");
const statusText = document.getElementById("statusText");
const results = document.getElementById("results");
const filesInput = document.getElementById("files");
filesInput.addEventListener("change", () => {
  const fileNameSpan = document.getElementById("fileName");
  if (filesInput.files.length > 1) {
    fileNameSpan.textContent = `${filesInput.files.length} file dipilih`;
  } else if (filesInput.files.length === 1) {
    fileNameSpan.textContent = filesInput.files[0].name;
  } else {
    fileNameSpan.textContent = "Belum ada file dipilih";
  }
});




const convertBtn = document.getElementById("convertBtn");

const formats = {
  image: ["jpg", "jpeg", "png", "webp", "bmp", "gif", "tiff", "svg"],
  video: ["mp4", "avi", "mkv", "mov", "flv", "wmv"],
  audio: ["mp3", "wav", "flac", "ogg", "aac", "m4a"]
};

function updateFormats() {
  const mode = modeSelect.value;
  formatSelect.innerHTML = "";
  formats[mode].forEach(fmt => {
    const option = document.createElement("option");
    option.value = fmt;
    option.textContent = fmt.toUpperCase();
    formatSelect.appendChild(option);
  });
  filesInput.setAttribute("accept", formats[mode].map(f => "." + f).join(","));
}

modeSelect.addEventListener("change", updateFormats);
updateFormats();

document.getElementById("uploadForm").addEventListener("submit", function(e) {
  e.preventDefault();

  const mode = modeSelect.value;
  const files = filesInput.files;

  for (let file of files) {
    const ext = file.name.split(".").pop().toLowerCase();
    if (!formats[mode].includes(ext)) {
      alert(`File "${file.name}" bukan format ${mode} yang valid.`);
      return;
    }
  }

  convertBtn.disabled = true;
  progressBar.style.width = "0%";
  progressBar.textContent = "0%";
  statusText.textContent = `Status: Upload ${files.length > 1 ? files.length + " file" : files[0].name}`;

  const formData = new FormData(this);

  fetch("/upload", { method: "POST", body: formData })
    .then(res => res.json())
    .then(data => {
      const batchId = data.batch_id;

      const interval = setInterval(() => {
        fetch("/progress")
          .then(res => res.json())
          .then(p => {
            progressBar.style.width = p.progress + "%";
            progressBar.textContent = p.progress + "%";

            if (p.status === "uploading") {
              statusText.textContent = `Status: Upload ${files.length > 1 ? files.length + " file" : files[0].name}`;
            } else if (p.status === "converting") {
              statusText.textContent = `Status: Converting ${files.length > 1 ? files.length + " file" : files[0].name}`;
            }

            if (p.status === "done") {
              clearInterval(interval);
              convertBtn.disabled = false;
              statusText.textContent = "Selesai";

              const batchDiv = document.createElement("div");
              batchDiv.classList.add("batch");

              const title = document.createElement("h3");
              title.textContent = `Batch ${batchId}`;
              batchDiv.appendChild(title);

              if (p.files.length > 1) {
                const zipBtn = document.createElement("a");
                zipBtn.href = `/download_zip/${batchId}`;
                zipBtn.textContent = "Download Semua (ZIP)";
                zipBtn.style.background = "#2196F3";
                zipBtn.style.color = "white";
                zipBtn.style.padding = "5px 10px";
                zipBtn.style.borderRadius = "5px";
                zipBtn.style.display = "inline-block";
                zipBtn.style.marginBottom = "10px";
                batchDiv.appendChild(zipBtn);
              }

             p.files.forEach(file => {
              const fileItem = document.createElement("div");
              fileItem.classList.add("file-item");

              const fileInfo = document.createElement("div");
              fileInfo.classList.add("file-info");

              const icon = document.createElement("i");
              icon.classList.add("fas", "fa-file-alt", "file-icon");

              const fileName = document.createElement("span");
              fileName.textContent = file;

              fileInfo.appendChild(icon);
              fileInfo.appendChild(fileName);

              const downloadBtn = document.createElement("a");
              downloadBtn.href = `/download/${batchId}/${file}`;
              downloadBtn.textContent = "Download";

              fileItem.appendChild(fileInfo);
              fileItem.appendChild(downloadBtn);

              batchDiv.appendChild(fileItem);
            });

              results.prepend(batchDiv);
            }
          });
      }, 500);
    });
});

const jobsContainer = document.getElementById("jobsContainer");
const role = window.SAFEHIRE_ROLE || "employer";

const modal = document.getElementById("messageModal");
const modalTitle = document.getElementById("modalTitle");
const modalMessage = document.getElementById("modalMessage");
const modalIcon = document.getElementById("modalIcon");
const modalOkBtn = document.getElementById("modalOkBtn");


function showModal(type, message) {
  if (type === "success") {
    modalTitle.textContent = "Success";
    modalMessage.textContent = message || "Action completed successfully.";
    modalIcon.textContent = "✓";
  } else {
    modalTitle.textContent = "Error";
    modalMessage.textContent = message || "Something went wrong.";
    modalIcon.textContent = "!";
  }

  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function closeModal() {
  modal.classList.remove("flex");
  modal.classList.add("hidden");
}

if (modalOkBtn) modalOkBtn.addEventListener("click", closeModal);

if (modal) {
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });
}


function getJobStatusBadge(status) {
  const value = (status || "").toLowerCase();

  if (value === "open") {
    return `<span class="px-3 py-1 text-sm rounded-full bg-emerald-500/20 text-emerald-300">Open</span>`;
  }

  if (value === "assigned") {
    return `<span class="px-3 py-1 text-sm rounded-full bg-pink-500/20 text-pink-300">Assigned</span>`;
  }

  if (value === "completed") {
    return `<span class="px-3 py-1 text-sm rounded-full bg-blue-500/20 text-blue-300">Completed</span>`;
  }

  return `<span class="px-3 py-1 text-sm rounded-full bg-white/10 text-white">${status}</span>`;
}

function renderRating(rating) {
  const value = Number(rating ?? 0).toFixed(1);
  return `⭐ ${value}`;
}


function getWorkerMatchBadge(worker) {
  if (worker.is_assigned || worker.application_status === "selected") {
    return `<span class="px-2 py-1 rounded-full text-xs bg-pink-500/20 text-pink-200">Hired</span>`;
  }

  if (worker.application_status === "suggested") {
    return `<span class="px-2 py-1 rounded-full text-xs bg-blue-500/20 text-blue-200">Best Match</span>`;
  }

  return `<span class="px-2 py-1 rounded-full text-xs bg-emerald-500/20 text-emerald-200">Applied</span>`;
}


function getEmployerViewCard(job, workers) {
  const workerHTML = workers.length
    ? workers.map((w) => `
        <div class="bg-white/10 p-4 rounded-xl border border-white/10">
          
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="font-semibold text-lg">${w.worker_name}</p>
              <p class="text-xs text-pink-200">${w.profession || "Worker"}</p>
            </div>
            ${getWorkerMatchBadge(w)}
          </div>
          <p class="text-sm text-gray-300">${w.skills}</p>
          <p class="text-sm text-white/70">Experience: ${w.experience ?? 0} years</p>
          <p class="text-yellow-300 font-semibold">${renderRating(w.rating)}</p>

          <p class="text-xs text-pink-300 font-medium mt-2">
            AI Match Score: ${w.score}
          </p>

          ${
            w.score > 80
              ? `<p class="text-green-300 text-sm font-semibold mt-1">🔥 Top Match</p>`
              : ""
          }

          ${
            (job.status || "").toLowerCase() === "open"
              ? `
                <button onclick="hire(${job.job_id}, ${w.worker_id})"
                  class="mt-3 w-full bg-green-500 py-2 rounded-lg text-sm font-semibold hover:opacity-90">
                  Hire
                </button>
              `
              : `
                <button disabled
                  class="mt-3 w-full bg-gray-500 py-2 rounded-lg text-sm font-semibold opacity-70">
                  ${w.is_assigned || w.application_status === "selected" ? "Hired" : "Unavailable"}
                </button>
              `
          }

        </div>
      `).join("")
    : `<p class="text-gray-300">No strong verified worker matches yet.</p>`;

  return `
    <div class="bg-white/10 p-5 rounded-2xl border border-white/10">
      
      <div class="flex justify-between">
        <div>
          <h3 class="text-xl font-bold">${job.job_title}</h3>
          <p class="text-sm text-gray-300">${job.job_category} • ${job.job_location}</p>
        </div>
        ${getJobStatusBadge(job.status)}
      </div>

      <p class="mt-2 text-lg font-semibold">BDT ${job.budget}</p>
      <p class="text-sm text-white/70">Applicants: ${job.applicant_count ?? 0}</p>

      <div class="mt-4 space-y-3">
        ${workerHTML}
      </div>

    </div>
  `;
}


function getAdminViewCard(job) {
  return `
    <div class="bg-white/10 p-5 rounded-2xl border border-white/10">
      
      <div class="flex justify-between">
        <div>
          <h3 class="text-xl font-bold">${job.title}</h3>
          <p class="text-sm text-gray-300">${job.category} • ${job.location}</p>
        </div>
        ${getJobStatusBadge(job.status)}
      </div>

      <p class="mt-2 font-semibold">BDT ${job.budget}</p>
      <p class="text-sm mt-2">${job.description || "No description"}</p>

    </div>
  `;
}


async function loadJobs() {
  try {
    jobsContainer.innerHTML = `<p>Loading jobs...</p>`;

    if (role === "admin") {
      const res = await fetch("/jobs_api");
      const jobs = await res.json();

      jobsContainer.innerHTML = jobs.map(getAdminViewCard).join("");
      return;
    }

    const res = await fetch("/job_matches");
    const jobs = await res.json();

    jobsContainer.innerHTML = jobs
      .map((job) => getEmployerViewCard(job, job.top_matches || []))
      .join("");

  } catch (error) {
    console.error(error);
    jobsContainer.innerHTML = `<p>Failed to load jobs</p>`;
  }
}


async function hire(jobId, workerId) {
  try {
    const res = await fetch("/hire", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: jobId, worker_id: workerId })
    });

    const data = await res.json();

    if (!res.ok) {
      showModal("error", data.error);
      return;
    }

    showModal("success", data.message);
    loadJobs();

  } catch (error) {
    showModal("error", "Something went wrong");
  }
}

window.hire = hire;


loadJobs();

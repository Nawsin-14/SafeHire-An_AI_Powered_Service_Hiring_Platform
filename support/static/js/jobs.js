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
    modalIcon.className =
      "w-14 h-14 rounded-2xl flex items-center justify-center text-2xl font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30";
  } else {
    modalTitle.textContent = "Error";
    modalMessage.textContent = message || "Something went wrong.";
    modalIcon.textContent = "!";
    modalIcon.className =
      "w-14 h-14 rounded-2xl flex items-center justify-center text-2xl font-bold bg-rose-500/20 text-rose-300 border border-rose-400/30";
  }

  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function closeModal() {
  modal.classList.remove("flex");
  modal.classList.add("hidden");
}

if (modalOkBtn) {
  modalOkBtn.addEventListener("click", closeModal);
}

if (modal) {
  modal.addEventListener("click", function (e) {
    if (e.target === modal) {
      closeModal();
    }
  });
}

function getJobStatusBadge(status) {
  const value = (status || "").toLowerCase();

  if (value === "open") {
    return `
      <span class="text-sm px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300">
        Open
      </span>
    `;
  }

  if (value === "assigned") {
    return `
      <span class="text-sm px-3 py-1 rounded-full bg-pink-500/20 text-pink-300">
        Assigned
      </span>
    `;
  }

  if (value === "completed") {
    return `
      <span class="text-sm px-3 py-1 rounded-full bg-blue-500/20 text-blue-300">
        Completed
      </span>
    `;
  }

  return `
    <span class="text-sm px-3 py-1 rounded-full bg-white/10 text-white/80">
      ${status || "Unknown"}
    </span>
  `;
}

function renderRating(rating) {
  const value = Number(rating ?? 0).toFixed(1);
  return `<span class="text-yellow-300 font-semibold">⭐ ${value}</span>`;
}

function getEmployerViewCard(job, workers) {
  const workerHTML = workers.length
    ? workers.map((w) => `
      <div class="bg-white/10 p-4 rounded-xl border border-white/10">
        <div class="flex justify-between items-start gap-3">
          <div>
            <p class="font-semibold text-lg">${w.worker_name}</p>
            <p class="text-sm text-gray-300 mt-1">${w.skills}</p>
            <p class="text-sm text-white/70 mt-1">Experience: ${w.experience ?? 0} years</p>
            <p class="text-sm mt-1">${renderRating(w.rating)}</p>
            <p class="text-xs text-pink-300 mt-2 font-medium">AI Match Score: ${w.score}</p>
          </div>

          <div class="text-right">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-400/20">
              Applicant
            </span>
          </div>
        </div>

        ${
          (job.status || "").toLowerCase() === "open"
            ? `
              <button
                onclick="hire(${job.job_id}, ${w.worker_id})"
                class="mt-3 w-full bg-green-500 py-2 rounded-lg text-sm font-semibold hover:opacity-90">
                Hire
              </button>
            `
            : `
              <button
                disabled
                class="mt-3 w-full bg-gray-500 py-2 rounded-lg text-sm font-semibold cursor-not-allowed opacity-70">
                Already Assigned
              </button>
            `
        }
      </div>
    `).join("")
    : `
      <div class="bg-white/5 p-4 rounded-xl border border-white/10">
        <p class="text-gray-300 text-sm">No verified applicants yet for this job.</p>
      </div>
    `;

  return `
    <div class="bg-white/10 backdrop-blur p-5 rounded-2xl border border-white/10 shadow-lg">
      <div class="flex justify-between items-start gap-4">
        <div>
          <h3 class="text-xl font-bold">${job.job_title}</h3>
          <p class="text-sm text-gray-300">${job.job_category} • ${job.job_location}</p>
        </div>
        ${getJobStatusBadge(job.status)}
      </div>

      <div class="mt-3 flex items-center justify-between gap-4 flex-wrap">
        <p class="text-lg font-semibold">BDT ${job.budget}</p>
        <p class="text-sm text-white/70">Applicants: ${job.applicant_count ?? 0}</p>
      </div>

      <div class="mt-4 space-y-3">
        ${workerHTML}
      </div>
    </div>
  `;
}

function getAdminViewCard(job) {
  return `
    <div class="bg-white/10 backdrop-blur p-5 rounded-2xl border border-white/10 shadow-lg">
      <div class="flex justify-between items-start gap-4">
        <div>
          <h3 class="text-xl font-bold">${job.title}</h3>
          <p class="text-sm text-gray-300">${job.category} • ${job.location}</p>
        </div>
        ${getJobStatusBadge(job.status)}
      </div>

      <p class="mt-3 text-lg font-semibold">BDT ${job.budget}</p>

      <p class="mt-4 text-sm text-white/80">
        ${job.description ? job.description : "No description provided"}
      </p>

      <div class="mt-4 pt-4 border-t border-white/10 flex items-center justify-between">
        <p class="text-xs text-gray-300">Job ID: ${job.id}</p>
      </div>
    </div>
  `;
}

async function loadJobs() {
  try {
    jobsContainer.innerHTML = `
      <div class="col-span-full bg-white/10 backdrop-blur p-6 rounded-2xl border border-white/10 text-white/70">
        Loading jobs...
      </div>
    `;

    if (role === "admin") {
      const res = await fetch("/jobs_api", { credentials: "include" });
      const jobs = await res.json();

      if (!res.ok) {
        throw new Error(jobs.error || "Failed to load jobs");
      }

      if (!Array.isArray(jobs) || jobs.length === 0) {
        jobsContainer.innerHTML = `
          <div class="col-span-full bg-white/10 backdrop-blur p-6 rounded-2xl border border-white/10 text-white/70">
            No jobs found
          </div>
        `;
        return;
      }

      jobsContainer.innerHTML = jobs.map((job) => getAdminViewCard(job)).join("");
      return;
    }

    const res = await fetch("/job_matches", { credentials: "include" });
    const jobs = await res.json();

    if (!res.ok) {
      throw new Error(jobs.error || "Failed to load jobs");
    }

    if (!Array.isArray(jobs) || jobs.length === 0) {
      jobsContainer.innerHTML = `
        <div class="col-span-full bg-white/10 backdrop-blur p-6 rounded-2xl border border-white/10 text-white/70">
          No jobs found
        </div>
      `;
      return;
    }

    jobsContainer.innerHTML = jobs
      .map((job) => getEmployerViewCard(job, job.top_matches || []))
      .join("");

  } catch (error) {
    console.error(error);
    jobsContainer.innerHTML = `
      <div class="col-span-full bg-white/10 backdrop-blur p-6 rounded-2xl border border-white/10 text-red-300">
        Failed to load jobs
      </div>
    `;
  }
}

async function hire(jobId, workerId) {
  if (role === "admin") {
    showModal("error", "Admin cannot hire workers.");
    return;
  }

  try {
    const res = await fetch("/hire", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: jobId, worker_id: workerId })
    });

    const data = await res.json();

    if (!res.ok) {
      showModal("error", data.error || "Failed to hire worker");
      return;
    }

    showModal("success", data.message || "Worker hired successfully");
    loadJobs();

  } catch (error) {
    console.error(error);
    showModal("error", "Something went wrong");
  }
}

window.hire = hire;

loadJobs();
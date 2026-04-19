const availableJobs = document.getElementById("availableJobs");
const myApplications = document.getElementById("myApplications");

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

function applicationBadge(status) {
  const value = (status || "").toLowerCase();

  if (value === "selected") {
    return `<span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-400/20">Selected</span>`;
  }

  if (value === "rejected") {
    return `<span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-rose-500/20 text-rose-300 border border-rose-400/20">Rejected</span>`;
  }

  return `<span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-amber-500/20 text-amber-300 border border-amber-400/20">Applied</span>`;
}

async function loadAvailableJobs() {
  if (!availableJobs) return;

  try {
    const res = await fetch("/worker_jobs");
    const jobs = await res.json();

    if (!res.ok) {
      throw new Error(jobs.error || "Failed to load jobs");
    }

    if (!Array.isArray(jobs) || jobs.length === 0) {
      availableJobs.innerHTML = `
        <div class="md:col-span-2 text-center py-8">
          <p class="text-white font-medium">No matching jobs available right now.</p>
          <p class="text-sm text-gray-400 mt-1">When employers post jobs matching your skills, they will appear here.</p>
        </div>
      `;
      return;
    }

    availableJobs.innerHTML = "";

    jobs.forEach((job) => {
      availableJobs.innerHTML += `
        <div class="bg-white/5 border border-white/10 rounded-2xl p-5">
          <div class="flex items-start justify-between gap-4">
            <div>
              <h3 class="text-lg font-semibold">${job.title}</h3>
              <p class="text-sm text-gray-300 mt-1">${job.category} • ${job.location}</p>
            </div>
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-400/20">
              Open
            </span>
          </div>

          <p class="text-sm text-gray-400 mt-3">${job.description || "No description provided."}</p>

          <p class="text-xs text-pink-300 mt-2 font-medium">
            AI Match Score: ${job.score}
          </p>

          <div class="mt-4 flex items-center justify-between gap-4">
            <p class="text-lg font-bold">BDT ${job.budget}</p>

            ${
              job.already_applied
                ? `<button disabled class="px-4 py-2 rounded-xl bg-gray-500 text-white text-sm font-semibold cursor-not-allowed opacity-70">Applied</button>`
                : `<button onclick="applyToJob(${job.id})" class="px-4 py-2 rounded-xl bg-gradient-to-r from-pink-500 to-purple-600 text-white text-sm font-semibold hover:opacity-90">Apply</button>`
            }
          </div>
        </div>
      `;
    });
  } catch (error) {
    console.error(error);
    availableJobs.innerHTML = `
      <div class="md:col-span-2 text-center py-8">
        <p class="text-rose-300 font-medium">Could not load matching jobs.</p>
      </div>
    `;
  }
}

async function applyToJob(jobId) {
  try {
    const res = await fetch("/apply_job", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ job_id: jobId })
    });

    const data = await res.json();

    if (!res.ok) {
      showModal("error", data.error || "Failed to apply");
      return;
    }

    showModal("success", data.message || "Applied successfully");
    loadAvailableJobs();
    loadMyApplications();
  } catch (error) {
    console.error(error);
    showModal("error", "Something went wrong while applying");
  }
}

async function loadMyApplications() {
  if (!myApplications) return;

  try {
    const res = await fetch("/my_applications");
    const apps = await res.json();

    if (!res.ok) {
      throw new Error(apps.error || "Failed to load applications");
    }

    if (!Array.isArray(apps) || apps.length === 0) {
      myApplications.innerHTML = `
        <div class="md:col-span-2 text-center py-8">
          <p class="text-white font-medium">No applications yet.</p>
          <p class="text-sm text-gray-400 mt-1">Jobs you apply to will appear here.</p>
        </div>
      `;
      return;
    }

    myApplications.innerHTML = "";

    apps.forEach((app) => {
      myApplications.innerHTML += `
        <div class="bg-white/5 border border-white/10 rounded-2xl p-5">
          <div class="flex items-start justify-between gap-4">
            <div>
              <h3 class="text-lg font-semibold">${app.title}</h3>
              <p class="text-sm text-gray-300 mt-1">${app.category} • ${app.location}</p>
            </div>
            ${applicationBadge(app.status)}
          </div>

          <p class="text-sm text-gray-400 mt-3">${app.description || "No description provided."}</p>

          <div class="mt-4 flex items-center justify-between gap-4">
            <p class="text-lg font-bold">BDT ${app.budget}</p>
            <span class="text-xs text-white/60 uppercase">${app.job_status}</span>
          </div>
        </div>
      `;
    });
  } catch (error) {
    console.error(error);
    myApplications.innerHTML = `
      <div class="md:col-span-2 text-center py-8">
        <p class="text-rose-300 font-medium">Could not load applications.</p>
      </div>
    `;
  }
}

window.applyToJob = applyToJob;

loadAvailableJobs();
loadMyApplications();
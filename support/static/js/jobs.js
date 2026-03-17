const jobList = document.getElementById("jobList");
const jobForm = document.getElementById("jobForm");
const hireForm = document.getElementById("hireForm");

function getStatusPillClass(status) {
  if (status === "assigned") {
    return "bg-amber-500/20 text-amber-300 border border-amber-400/20";
  }
  if (status === "completed") {
    return "bg-emerald-500/20 text-emerald-300 border border-emerald-400/20";
  }
  return "bg-pink-500/20 text-pink-300 border border-pink-400/20";
}

function getStatusLabel(status) {
  if (status === "assigned") return "Assigned";
  if (status === "completed") return "Completed";
  return "Open";
}

function renderJobs(jobs, matchMap = {}) {
  jobList.innerHTML = "";

  if (!Array.isArray(jobs) || jobs.length === 0) {
    jobList.innerHTML = `
      <div class="sm:col-span-2 text-center py-10">
        <p class="text-white font-medium">No jobs posted yet.</p>
        <p class="text-sm text-gray-300 mt-1">Post a job to see it listed here.</p>
      </div>
    `;
    return;
  }

  jobs.forEach((job) => {
    const match = matchMap[job.id];
    const hasMatch = match && match.worker_id;

    jobList.innerHTML += `
      <div class="bg-white/5 border border-white/10 rounded-3xl p-5 backdrop-blur transition hover:bg-white/10 hover:shadow-xl">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="font-semibold leading-5 text-white">${job.title}</p>
            <p class="text-sm text-gray-300 mt-1">${job.category} • ${job.location}</p>
          </div>

          <span class="px-3 py-1 rounded-full text-xs font-medium ${getStatusPillClass(job.status)}">
            ${getStatusLabel(job.status)}
          </span>
        </div>

        <p class="text-sm text-gray-300 mt-4">${job.description || "No description provided."}</p>
        <div class="mt-4 p-4 rounded-2xl bg-purple-500/10 border border-purple-400/20">
          <div class="flex items-center justify-between gap-2">
            <p class="text-xs font-semibold text-purple-200 uppercase tracking-wide">AI Match Recommendation</p>
            ${
              hasMatch
                ? `<span class="px-2 py-1 rounded-full text-[10px] font-semibold bg-purple-500/20 text-purple-200 border border-purple-400/20">Best Match</span>`
                : ""
            }
          </div>


          <p class="text-sm text-white mt-2">
            ${hasMatch ? match.matched_worker : "No suitable worker found"}
          </p>

          ${
            hasMatch
              ? `
                <p class="text-xs text-gray-300 mt-1">Worker ID: ${match.worker_id}</p>
                <p class="text-xs text-gray-300 mt-1">Match Score: ${match.score}/100</p>
              `
              : `<p class="text-xs text-gray-400 mt-1">No verified worker matched this job yet.</p>`
          }
        </div>

        <div class="mt-4 pt-4 border-t border-white/10 flex items-center justify-between">
          <p class="text-sm font-medium text-white">Budget: ৳${job.budget}</p>
          <p class="text-xs text-gray-300">Job ID: ${job.id}</p>
        </div>
      </div>
    `;
  });
}

async function loadJobs() {
  try {
    const [jobsResponse, matchesResponse] = await Promise.all([
      fetch("/jobs_api"),
      fetch("/job_matches")
    ]);

    if (!jobsResponse.ok) throw new Error(`Jobs HTTP ${jobsResponse.status}`);
    if (!matchesResponse.ok) throw new Error(`Matches HTTP ${matchesResponse.status}`);

    const jobs = await jobsResponse.json();
    const matches = await matchesResponse.json();

    const matchMap = {};
    matches.forEach((m) => {
      matchMap[m.job_id] = m;
    });

    renderJobs(jobs, matchMap);
  } catch (error) {
    console.error("Error loading jobs:", error);
    jobList.innerHTML = `
      <div class="sm:col-span-2 text-center py-10">
        <p class="text-rose-300 font-medium">Could not load jobs.</p>
      </div>
    `;
  }
}

jobForm.addEventListener("submit", async function (e) {
  e.preventDefault();

  const formData = {
    title: this.title.value.trim(),
    category: this.category.value.trim(),
    location: this.location.value.trim(),
    budget: this.budget.value.trim(),
    description: this.description.value.trim()
  };

  try {
    const response = await fetch("/add_job", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(formData)
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Failed to post job");
    }

    alert(data.message || "Job posted successfully");
    this.reset();
    loadJobs();
  } catch (error) {
    console.error("Error posting job:", error);
    alert(error.message || "Could not post job");
  }
});

hireForm.addEventListener("submit", async function (e) {
  e.preventDefault();

  const formData = {
    employer_name: this.employer_name.value.trim(),
    job_id: this.job_id.value.trim(),
    worker_id: this.worker_id.value.trim()
  };

  try {
    const response = await fetch("/hire", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(formData)
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Failed to hire worker");
    }

    alert(data.message || "Worker hired successfully");
    this.reset();
    loadJobs();
  } catch (error) {
    console.error("Error hiring worker:", error);
    alert(error.message || "Could not hire worker");
  }
});

 loadJobs();
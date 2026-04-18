const loading = document.getElementById("loading");
const workersTable = document.getElementById("workersTable");
const workersBody = document.getElementById("workersBody");
const emptyState = document.getElementById("emptyState");
const refreshBtn = document.getElementById("refreshBtn");

const modal = document.getElementById("messageModal");
const modalTitle = document.getElementById("modalTitle");
const modalMessage = document.getElementById("modalMessage");
const modalIcon = document.getElementById("modalIcon");
const modalOkBtn = document.getElementById("modalOkBtn");

function getStatusBadge(status) {
  const value = (status || "").toLowerCase();

  if (value === "verified") {
    return `<span class="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">Verified</span>`;
  }

  if (value === "rejected") {
    return `<span class="inline-flex rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-700">Rejected</span>`;
  }

  return `<span class="inline-flex rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">Pending</span>`;
}

function showModal(type, message) {
  if (type === "success") {
    modalTitle.textContent = "Success";
    modalMessage.textContent = message || "Worker verification updated successfully.";
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

modalOkBtn.addEventListener("click", closeModal);

modal.addEventListener("click", function (e) {
  if (e.target === modal) {
    closeModal();
  }
});

async function updateWorkerStatus(workerId, status) {
  try {
    const res = await fetch(`/verify_worker/${workerId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ status })
    });

    const data = await res.json();

    if (!res.ok) {
      showModal("error", data.error || "Failed to update worker status");
      return;
    }

    await loadWorkers();
    showModal("success", data.message || "Worker verification updated successfully");
  } catch (error) {
    console.error(error);
    showModal("error", "Something went wrong while updating worker status");
  }
}

async function loadWorkers() {
  loading.classList.remove("hidden");
  workersTable.classList.add("hidden");
  emptyState.classList.add("hidden");
  workersBody.innerHTML = "";

  try {
    const response = await fetch("/workers");
    const workers = await response.json();

    loading.classList.add("hidden");

    if (!response.ok) {
      throw new Error(workers.error || `HTTP ${response.status}`);
    }

    if (!Array.isArray(workers) || workers.length === 0) {
      emptyState.classList.remove("hidden");
      return;
    }

    workersTable.classList.remove("hidden");

    workers.forEach((worker) => {
      const row = document.createElement("tr");
      row.className = "hover:bg-white/5";

      row.innerHTML = `
        <td class="px-6 py-4 text-sm">${worker.id ?? ""}</td>
        <td class="px-6 py-4 text-sm font-semibold">${worker.name ?? ""}</td>
        <td class="px-6 py-4 text-sm">${worker.nid ?? ""}</td>
        <td class="px-6 py-4 text-sm">${worker.phone ?? ""}</td>
        <td class="px-6 py-4 text-sm">${worker.address ?? ""}</td>
        <td class="px-6 py-4 text-sm">${worker.skills ?? ""}</td>
        <td class="px-6 py-4 text-sm text-center">${worker.experience ?? 0} years</td>
        <td class="px-6 py-4 text-sm text-center">${worker.rating ?? 0}</td>
        <td class="px-6 py-4 text-sm text-center">${worker.risk_score ?? 0}</td>
        <td class="px-6 py-4 text-sm text-center">${getStatusBadge(worker.verification_status)}</td>
        <td class="px-6 py-4 text-sm text-center">
          <div class="flex justify-center gap-2 flex-wrap">
            <button
              onclick="updateWorkerStatus(${worker.id}, 'Verified')"
              class="bg-gradient-to-r from-pink-500 to-purple-600 px-3 py-1 rounded text-xs text-white hover:opacity-90 transition">
              Verify
            </button>

            <button
              onclick="updateWorkerStatus(${worker.id}, 'Rejected')"
              class="bg-rose-500/90 px-3 py-1 rounded text-xs text-white hover:bg-rose-500 transition">
              Reject
            </button>

            <button
              onclick="updateWorkerStatus(${worker.id}, 'Pending')"
              class="bg-white/10 border border-white/10 px-3 py-1 rounded text-xs text-white hover:bg-white/20 transition">
              Pending
            </button>
          </div>
        </td>
      `;

      workersBody.appendChild(row);
    });
  } catch (error) {
    console.error(error);
    loading.textContent = "Failed to load workers.";
  }
}

refreshBtn.addEventListener("click", loadWorkers);

window.updateWorkerStatus = updateWorkerStatus;

loadWorkers();
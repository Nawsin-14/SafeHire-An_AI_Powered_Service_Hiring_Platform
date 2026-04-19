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
    return `<span class="px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-400/20">Verified</span>`;
  }

  if (value === "rejected") {
    return `<span class="px-3 py-1 rounded-full text-xs font-medium bg-rose-500/20 text-rose-300 border border-rose-400/20">Rejected</span>`;
  }

  return `<span class="px-3 py-1 rounded-full text-xs font-medium bg-amber-500/20 text-amber-300 border border-amber-400/20">Pending</span>`;
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
      row.className = "hover:bg-white/5 transition";

      row.innerHTML = `
        <td class="px-6 py-4">${worker.id ?? ""}</td>

        <td class="px-6 py-4 font-semibold text-white">
          ${worker.name ?? ""}
        </td>

        <td class="px-6 py-4 text-white/80">
          ${worker.nid ?? ""}
        </td>

        <td class="px-6 py-4 text-white/80">
          ${worker.phone ?? ""}
        </td>

        <td class="px-6 py-4 text-white/80">
          ${worker.address ?? ""}
        </td>

        <td class="px-6 py-4 text-white/80">
          ${worker.skills ?? ""}
        </td>

        <td class="px-6 py-4 text-center">
          ${worker.experience ?? 0} yrs
        </td>

        <td class="px-6 py-4 text-center text-yellow-300 font-semibold">
          ⭐ ${worker.rating ?? 0}
        </td>

        <td class="px-6 py-4 text-center text-pink-300 font-semibold">
          ${worker.risk_score ?? 0}
        </td>

        <td class="px-6 py-4 text-center">
          ${getStatusBadge(worker.verification_status)}
        </td>

        <td class="px-6 py-4 text-center">
          <div class="flex justify-center gap-2 flex-wrap">

            <button
              onclick="updateWorkerStatus(${worker.id}, 'Verified')"
              class="bg-gradient-to-r from-pink-500 to-purple-600 px-3 py-1 rounded-lg text-xs font-semibold hover:opacity-90 transition">
              Verify
            </button>

            <button
              onclick="updateWorkerStatus(${worker.id}, 'Rejected')"
              class="bg-rose-500 px-3 py-1 rounded-lg text-xs font-semibold hover:opacity-90 transition">
              Reject
            </button>

            <button
              onclick="updateWorkerStatus(${worker.id}, 'Pending')"
              class="bg-white/10 border border-white/10 px-3 py-1 rounded-lg text-xs font-semibold hover:bg-white/20 transition">
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
const { ipcRenderer } = require("electron");

let allProfiles = [];
let filteredProfiles = [];
let currentPage = 1;
let pageSize = 10;
let selectedProfiles = new Set();
let searchQuery = "";

window.onload = () => {
  log("应用已启动");
  refresh();
};

async function refresh() {
  try {
    log("正在刷新状态...");
    const status = await ipcRenderer.invoke("get-status");
    document.getElementById("current-profile").innerText =
      status.current_profile || "未命名 (外部设置)";
    document.getElementById("current-email").innerText =
      status.current_email || "Unknown";

    allProfiles = await ipcRenderer.invoke("get-list");
    applyFilterAndRender();
    log("刷新成功");
  } catch (err) {
    log("刷新失败: " + err);
  }
}

function applyFilterAndRender() {
  filteredProfiles = allProfiles.filter(
    (p) =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  document.getElementById("total-count").innerText = filteredProfiles.length;
  renderTable();
  renderPagination();
}

function renderTable() {
  const start = (currentPage - 1) * pageSize;
  const end = start + pageSize;
  const pageItems = filteredProfiles.slice(start, end);

  const tbody = document.getElementById("profile-table-body");
  const emptyState = document.getElementById("empty-state");

  tbody.innerHTML = "";

  if (pageItems.length === 0) {
    emptyState.classList.remove("hidden");
  } else {
    emptyState.classList.add("hidden");
    pageItems.forEach((profile) => {
      const tr = document.createElement("tr");
      tr.className = `hover:bg-slate-50 transition-colors ${profile.is_current ? "bg-blue-50/30" : ""}`;
      tr.innerHTML = `
                <td class="p-4"><input type="checkbox" class="profile-checkbox rounded border-slate-300 text-blue-600 focus:ring-blue-500" data-name="${profile.name}" ${selectedProfiles.has(profile.name) ? "checked" : ""}></td>
                <td class="p-4">
                    <div class="profile-name-container flex items-center group cursor-pointer" onclick="startRename(this, '${profile.name}')">
                        <div class="font-medium text-slate-700 name-text">${profile.name}</div>
                        <svg class="w-3.5 h-3.5 ml-2 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
                        </svg>
                    </div>
                </td>
                <td class="p-4 text-slate-500 text-sm">${profile.email}</td>
                <td class="p-4">
                    ${
                      profile.is_current
                        ? '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">当前激活</span>'
                        : `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-500">${profile.last_active || "从未激活"}</span>`
                    }
                </td>
                <td class="p-4 text-right">
                    <div class="flex justify-end gap-2">
                        <button onclick="handleSwitch('${profile.name}')" class="p-1.5 text-blue-600 hover:bg-blue-50 rounded-md transition-colors" title="切换">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path></svg>
                        </button>
                        <button onclick="handleDelete('${profile.name}')" class="p-1.5 text-rose-600 hover:bg-rose-50 rounded-md transition-colors" title="删除">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                        </button>
                    </div>
                </td>
            `;
      tbody.appendChild(tr);
    });
  }

  // Bind checkboxes
  document.querySelectorAll(".profile-checkbox").forEach((cb) => {
    cb.onchange = (e) => {
      const name = e.target.getAttribute("data-name");
      if (e.target.checked) selectedProfiles.add(name);
      else selectedProfiles.delete(name);
      updateBatchButton();
    };
  });
}

function renderPagination() {
  const totalPages = Math.ceil(filteredProfiles.length / pageSize);
  const container = document.getElementById("pagination-controls");
  container.innerHTML = "";

  if (totalPages <= 1) return;

  for (let i = 1; i <= totalPages; i++) {
    const btn = document.createElement("button");
    btn.innerText = i;
    btn.className = `px-3 py-1 rounded-md text-sm font-medium transition-all ${i === currentPage ? "bg-blue-600 text-white" : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"}`;
    btn.onclick = () => {
      currentPage = i;
      renderTable();
      renderPagination();
    };
    container.appendChild(btn);
  }
}

function updateBatchButton() {
  const btn = document.getElementById("btn-batch-delete");
  const count = document.getElementById("selected-count");
  if (selectedProfiles.size > 0) {
    btn.classList.remove("hidden");
    count.innerText = selectedProfiles.size;
  } else {
    btn.classList.add("hidden");
  }
}

function log(msg) {
  const logEl = document.getElementById("log");
  const now = new Date().toLocaleTimeString();
  const p = document.createElement("p");
  p.className = "mb-1";
  p.innerHTML = `<span class="opacity-40">[${now}]</span> ${msg}`;
  logEl.appendChild(p);
  logEl.scrollTop = logEl.scrollHeight;
}

// Global Handlers
window.startRename = (container, oldName) => {
  if (container.querySelector("input")) return;

  const textEl = container.querySelector(".name-text");
  const originalContent = container.innerHTML;

  const input = document.createElement("input");
  input.type = "text";
  input.value = oldName;
  input.className =
    "w-full px-2 py-1 text-sm border border-blue-400 rounded focus:outline-none focus:ring-2 focus:ring-blue-200";

  container.innerHTML = "";
  container.appendChild(input);
  input.focus();
  input.select();

  const finish = async (save) => {
    const newName = input.value.trim();
    if (save && newName && newName !== oldName) {
      try {
        log(`正在将 ${oldName} 重命名为 ${newName}...`);
        await ipcRenderer.invoke("rename-profile", oldName, newName);
        log("重命名成功");
        await refresh();
      } catch (err) {
        log(`重命名失败: ${err}`);
        container.innerHTML = originalContent;
      }
    } else {
      container.innerHTML = originalContent;
    }
  };

  input.onkeydown = (e) => {
    if (e.key === "Enter") finish(true);
    if (e.key === "Escape") finish(false);
  };

  input.onblur = () => finish(true);
};

window.handleSwitch = async (name) => {
  setButtonsEnabled(false);
  log(`正在切换到 ${name}...`);
  try {
    await ipcRenderer.invoke("switch-profile", name);
    log(`成功切换到 ${name}`);
    await refresh();
  } catch (err) {
    log(`切换失败: ${err}`);
  } finally {
    setButtonsEnabled(true);
  }
};

window.handleDelete = async (name) => {
  if (!confirm(`确定要删除配置 "${name}" 吗？`)) return;
  try {
    await ipcRenderer.invoke("delete-profile", name);
    log(`已删除 ${name}`);
    selectedProfiles.delete(name);
    await refresh();
  } catch (err) {
    log(`删除失败: ${err}`);
  }
};

// Modal Logic
const logsModal = document.getElementById("logs-modal");
const addAccountModal = document.getElementById("add-account-modal");

document.getElementById("btn-show-logs").onclick = () =>
  logsModal.classList.remove("hidden");
document.getElementById("btn-close-logs").onclick = () =>
  logsModal.classList.add("hidden");
document.getElementById("btn-close-add-modal").onclick = () =>
  addAccountModal.classList.add("hidden");

// Close modals when clicking outside
window.onclick = (event) => {
  if (event.target === logsModal) logsModal.classList.add("hidden");
  if (event.target === addAccountModal) addAccountModal.classList.add("hidden");
};

// Event Listeners
document.getElementById("btn-refresh").onclick = refresh;

document.getElementById("search-input").oninput = (e) => {
  searchQuery = e.target.value;
  currentPage = 1;
  applyFilterAndRender();
};

document.getElementById("page-size-select").onchange = (e) => {
  pageSize = parseInt(e.target.value);
  currentPage = 1;
  applyFilterAndRender();
};
document.getElementById("select-all").onchange = (e) => {
  const isChecked = e.target.checked;
  const start = (currentPage - 1) * pageSize;
  const end = start + pageSize;
  const pageItems = filteredProfiles.slice(start, end);

  pageItems.forEach((p) => {
    if (isChecked) selectedProfiles.add(p.name);
    else selectedProfiles.delete(p.name);
  });

  renderTable();
  updateBatchButton();
};

document.getElementById("btn-save").onclick = () => {
  document.getElementById("new-profile-name").value = "";
  addAccountModal.classList.remove("hidden");
};

document.getElementById("btn-confirm-save").onclick = async () => {
  const name = document.getElementById("new-profile-name").value.trim();
  if (!name) {
    alert("请输入配置名称");
    return;
  }

  addAccountModal.classList.add("hidden");
  setButtonsEnabled(false);
  log(`正在保存当前账号为 ${name}...`);
  try {
    await ipcRenderer.invoke("save-profile", name);
    log(`账号已保存为: ${name}`);
    await refresh();
  } catch (err) {
    log(`保存失败: ${err}`);
  } finally {
    setButtonsEnabled(true);
  }
};

document.getElementById("btn-batch-delete").onclick = async () => {
  const count = selectedProfiles.size;
  if (!confirm(`确定要批量删除选中的 ${count} 个配置吗？`)) return;

  setButtonsEnabled(false);
  log(`正在批量删除 ${count} 个账号...`);
  try {
    await ipcRenderer.invoke("delete-profiles", Array.from(selectedProfiles));
    log(`成功删除 ${count} 个账号`);
    selectedProfiles.clear();
    document.getElementById("select-all").checked = false;
    await refresh();
  } catch (err) {
    log(`批量删除失败: ${err}`);
  } finally {
    setButtonsEnabled(true);
    updateBatchButton();
  }
};

document.getElementById("btn-reset").onclick = async () => {
  if (!confirm("确定要重置当前账号吗？这会生成新的机器 ID 并清除登录状态。"))
    return;

  setButtonsEnabled(false);
  log("正在重置当前账号并生成新 ID...");
  try {
    await ipcRenderer.invoke("reset-account");
    log("重置成功！已为您生成全新的机器 ID 环境。");
    await refresh();
  } catch (err) {
    log("重置失败: " + err);
  } finally {
    setButtonsEnabled(true);
  }
};

document.getElementById("btn-export").onclick = async () => {
  try {
    const result = await ipcRenderer.invoke("export-profiles");
    if (result) log("批量导出成功");
  } catch (err) {
    log("导出失败: " + err);
  }
};

document.getElementById("btn-import").onclick = async () => {
  try {
    const result = await ipcRenderer.invoke("import-profiles");
    if (result) {
      log("批量导入成功");
      await refresh();
    }
  } catch (err) {
    log("导入失败: " + err);
  }
};

function setButtonsEnabled(enabled) {
  document.querySelectorAll("button").forEach((btn) => {
    btn.disabled = !enabled;
    if (!enabled) btn.classList.add("opacity-50", "cursor-not-allowed");
    else btn.classList.remove("opacity-50", "cursor-not-allowed");
  });
}

// Init
refresh();

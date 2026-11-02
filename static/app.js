let currentTargetApp = null;
let activeCategory = "All";
let libraryApps = [];
let localIpas = [];

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  fetchDevices();
  fetchLocalIpas();
  fetchLibraryApps();
  fetchRefreshStatus();
  setupModal();
  setupSearch();

  const headerDev = document.getElementById("header-device-select");
  if (headerDev) {
    headerDev.addEventListener("change", (e) => {
      selectedDeviceUdid = e.target.value;
      const modalDev = document.getElementById("modal-device");
      if (modalDev) modalDev.value = selectedDeviceUdid;
      
      const currentDev = connectedDevices.find(d => d.udid === selectedDeviceUdid);
      const wifiBadge = document.getElementById("wifi-badge");
      if (wifiBadge && currentDev) {
        wifiBadge.innerText = currentDev.connection === "USB" ? "USB Connected" : "Wi-Fi Ready";
      }
    });
  }

  const btnRefreshDevs = document.getElementById("btn-refresh-devices");
  if (btnRefreshDevs) {
    btnRefreshDevs.addEventListener("click", () => {
      fetchDevices();
    });
  }

  // Poll devices every 10 seconds
  setInterval(fetchDevices, 10000);
});

// MARK: - Tabs
function initTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      
      const target = tab.getAttribute("data-tab");
      document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");
      document.getElementById(`tab-${target}`).style.display = "block";
    });
  });

  // Category filter pills in Library
  const pills = document.querySelectorAll(".cat-pill");
  pills.forEach(pill => {
    pill.addEventListener("click", () => {
      pills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      activeCategory = pill.getAttribute("data-cat");
      renderLibrary(libraryApps);
    });
  });
}

// MARK: - Device Info
let connectedDevices = [];
let selectedDeviceUdid = "";

async function fetchDevices() {
  const headerSelect = document.getElementById("header-device-select");
  const modalSelect = document.getElementById("modal-device");
  const wifiBadge = document.getElementById("wifi-badge");
  
  try {
    const res = await fetch("/api/devices");
    const data = await res.json();
    connectedDevices = data.devices || [];
    
    if (connectedDevices.length > 0) {
      if (!selectedDeviceUdid) {
        selectedDeviceUdid = connectedDevices[0].udid;
      }
      
      const optionsHtml = connectedDevices.map(d => 
        `<option value="${escapeHtml(d.udid)}" ${d.udid === selectedDeviceUdid ? 'selected' : ''}>${escapeHtml(d.name)}</option>`
      ).join("") + `<option value="auto">Auto-detect next device</option>`;
      
      if (headerSelect) headerSelect.innerHTML = optionsHtml;
      if (modalSelect) modalSelect.innerHTML = optionsHtml;
      
      const currentDev = connectedDevices.find(d => d.udid === selectedDeviceUdid) || connectedDevices[0];
      if (wifiBadge) {
        wifiBadge.innerText = currentDev.connection === "USB" ? "USB Connected" : "Wi-Fi Ready";
      }
    } else {
      const fallbackHtml = `<option value="00008110-001C7C163628201E">Soli's iPhone 14 (Wi-Fi)</option>`;
      if (headerSelect) headerSelect.innerHTML = fallbackHtml;
      if (modalSelect) modalSelect.innerHTML = fallbackHtml;
    }
  } catch (e) {
    console.log("Device error:", e);
  }
}

// MARK: - Local IPAs
async function fetchLocalIpas() {
  const container = document.getElementById("local-list");
  container.innerHTML = '<div style="color:#666;font-size:13px;padding:20px;">Scanning computer for IPAs...</div>';
  try {
    const res = await fetch("/api/local-ipas");
    const data = await res.json();
    localIpas = data.ipas || [];
    renderLocalIpas(localIpas);
  } catch (e) {
    container.innerHTML = `<div style="color:#ff4444;font-size:13px;padding:20px;">Failed to scan IPAs: ${e}</div>`;
  }
}

function renderLocalIpas(items) {
  const container = document.getElementById("local-list");
  if (!items || items.length === 0) {
    container.innerHTML = '<div style="color:#666;font-size:13px;padding:20px;">No .ipa files found. Use + Add Custom .IPA or browse Community Library.</div>';
    return;
  }
  
  container.innerHTML = items.map((item, idx) => `
    <div class="app-card" data-idx="${idx}">
      <div class="card-left">
        <img class="app-icon" src="${item.icon_url || '/static/default_icon.png'}" onerror="this.src='/static/default_icon.png'" alt="Icon" />
        <div class="card-meta">
          <h3>${escapeHtml(item.name)} <span class="version-tag">v${escapeHtml(item.version)}</span></h3>
          <div class="card-details">${escapeHtml(item.bundle_id)} · ${item.size_formatted} · ${escapeHtml(item.filename)}</div>
        </div>
      </div>
      <button class="btn btn-primary btn-sideload-local" data-idx="${idx}">Sideload</button>
    </div>
  `).join("");

  container.querySelectorAll(".app-card").forEach(card => {
    card.addEventListener("click", () => {
      const idx = parseInt(card.getAttribute("data-idx"), 10);
      if (localIpas[idx]) openSideloadModal(localIpas[idx], "local");
    });
  });

  container.querySelectorAll(".btn-sideload-local").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const idx = parseInt(btn.getAttribute("data-idx"), 10);
      if (localIpas[idx]) openSideloadModal(localIpas[idx], "local");
    });
  });
}

// MARK: - Community App Library
async function fetchLibraryApps() {
  try {
    const res = await fetch("/api/app-library");
    const data = await res.json();
    libraryApps = data.apps || [];
    renderLibrary(libraryApps);
  } catch (e) {
    console.log("Library error:", e);
  }
}

function renderLibrary(items) {
  const container = document.getElementById("library-list");
  const filtered = items.filter(a => activeCategory === "All" || a.category === activeCategory);
  
  container.innerHTML = filtered.map((app, idx) => `
    <div class="app-card" data-idx="${idx}">
      <div class="card-left">
        <img class="app-icon" src="${app.icon}" onerror="this.src='/static/default_icon.png'" alt="Icon" />
        <div class="card-meta">
          <h3>${escapeHtml(app.name)} <span class="version-tag">v${escapeHtml(app.version)}</span></h3>
          <div style="font-size:12px;color:#aaa;margin-bottom:3px;">${escapeHtml(app.description)}</div>
          <div class="card-details">${escapeHtml(app.category)} · Developer: ${escapeHtml(app.developer)}</div>
        </div>
      </div>
      <button class="btn btn-primary btn-sideload-lib" data-idx="${idx}">Install App</button>
    </div>
  `).join("");

  container.querySelectorAll(".app-card").forEach(card => {
    card.addEventListener("click", () => {
      const idx = parseInt(card.getAttribute("data-idx"), 10);
      if (filtered[idx]) openSideloadModal(filtered[idx], "library");
    });
  });

  container.querySelectorAll(".btn-sideload-lib").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const idx = parseInt(btn.getAttribute("data-idx"), 10);
      if (filtered[idx]) openSideloadModal(filtered[idx], "library");
    });
  });
}

// MARK: - 7-Day Refresh Status
async function fetchRefreshStatus() {
  try {
    const res = await fetch("/api/refresh-status");
    const data = await res.json();
    const container = document.getElementById("refresh-list");
    const apps = data.apps || [];
    
    if (apps.length === 0) {
      container.innerHTML = '<div style="color:#666;font-size:13px;padding:12px;">No sideloaded apps tracked yet. Sideload an app to enable auto-refresh.</div>';
      return;
    }

    container.innerHTML = apps.map(app => `
      <div class="refresh-card">
        <div>
          <div style="font-size:14px;font-weight:600;color:#fff;">${escapeHtml(app.name)} <span style="font-size:11px;color:#888;">(${escapeHtml(app.bundle_id)})</span></div>
          <div style="font-size:12px;color:#aaa;margin-top:2px;">Signed by: ${escapeHtml(app.apple_id)}</div>
          <div class="countdown-bar-wrapper">
            <div class="countdown-bar" style="width: ${app.percent_remaining}%;"></div>
          </div>
          <div style="font-size:11px;color:#888;margin-top:4px;font-family:ui-monospace,monospace;">
            ${app.days_remaining} days remaining (Expires in ${Math.round(app.days_remaining * 24)}h)
          </div>
        </div>
        <div>
          <button class="btn ${app.needs_refresh ? 'btn-primary' : ''}" onclick="refreshSingleApp('${escapeHtml(app.bundle_id)}')">
            ${app.needs_refresh ? 'Auto-Refresh Due' : 'Refresh Now'}
          </button>
        </div>
      </div>
    `).join("");
  } catch (e) {
    console.log("Refresh status error:", e);
  }
}

// MARK: - Modal & Sideload Execution
function setupModal() {
  const modal = document.getElementById("modal");
  const closeBtn = document.getElementById("modal-close-btn");
  const cancelBtn = document.getElementById("modal-cancel");
  const startBtn = document.getElementById("modal-start-btn");

  const close = () => modal.style.display = "none";
  closeBtn.addEventListener("click", close);
  cancelBtn.addEventListener("click", close);

  // Close when clicking overlay outside content
  modal.addEventListener("click", (e) => {
    if (e.target === modal) close();
  });

  startBtn.addEventListener("click", async () => {
    if (!currentTargetApp) return;
    startBtn.disabled = true;
    startBtn.innerText = "Sideloading...";
    
    const terminal = document.getElementById("modal-terminal");
    const statusBadge = document.getElementById("modal-status-badge");
    if (statusBadge) {
      statusBadge.innerText = "PROCESSING";
      statusBadge.style.background = "#332600";
      statusBadge.style.color = "#ffbd2e";
    }

    const timeNow = new Date().toLocaleTimeString();
    terminal.innerText += `\n\n[${timeNow}] >>> Starting deployment for ${currentTargetApp.name}...\n`;
    terminal.scrollTop = terminal.scrollHeight;
    
    const appleId = document.getElementById("modal-apple-id").value;
    const deviceSelect = document.getElementById("modal-device");
    const targetUdid = (deviceSelect && deviceSelect.value !== "auto") ? deviceSelect.value : null;
    
    try {
      const endpoint = currentTargetApp._type === "library" ? "/api/download-and-sideload" : "/api/sideload";
      const payload = currentTargetApp._type === "library" ? 
        { download_url: currentTargetApp.download_url, name: currentTargetApp.name, bundle_id: currentTargetApp.bundle_id, apple_id: appleId, udid: targetUdid } :
        { ipa_path: currentTargetApp.path, name: currentTargetApp.name, bundle_id: currentTargetApp.bundle_id, apple_id: appleId, udid: targetUdid };

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const result = await res.json();
      
      if (result.logs && result.logs.length > 0) {
        terminal.innerText += result.logs.join("\n") + "\n";
      }
      
      if (result.success) {
        terminal.innerText += `\n[${new Date().toLocaleTimeString()}] [+] [SUCCESS] App successfully installed and running on your device!\n`;
        if (statusBadge) {
          statusBadge.innerText = "SUCCESS";
          statusBadge.style.background = "#052e16";
          statusBadge.style.color = "#22c55e";
        }
        fetchRefreshStatus();
      } else {
        terminal.innerText += `\n[${new Date().toLocaleTimeString()}] [!] Installation error. Please verify USB cable or ensure iPhone screen is unlocked.\n`;
        if (statusBadge) {
          statusBadge.innerText = "FAILED";
          statusBadge.style.background = "#450a0a";
          statusBadge.style.color = "#ef4444";
        }
      }
    } catch (err) {
      terminal.innerText += `\n[${new Date().toLocaleTimeString()}] [ERROR] Connection failed: ${err}\n`;
      if (statusBadge) {
        statusBadge.innerText = "ERROR";
        statusBadge.style.background = "#450a0a";
        statusBadge.style.color = "#ef4444";
      }
    } finally {
      terminal.scrollTop = terminal.scrollHeight;
      startBtn.disabled = false;
      startBtn.innerText = "Start Sideload";
    }
  });
}

function openSideloadModal(item, type) {
  if (!item) return;
  item._type = type;
  currentTargetApp = item;

  const modalDevSelect = document.getElementById("modal-device");
  if (modalDevSelect && selectedDeviceUdid) {
    modalDevSelect.value = selectedDeviceUdid;
  }
  const selectedName = (modalDevSelect && modalDevSelect.selectedOptions && modalDevSelect.selectedOptions[0]) 
    ? modalDevSelect.selectedOptions[0].text 
    : "selected iPhone";

  document.getElementById("modal-title").innerText = item.name;
  document.getElementById("modal-sub").innerText = item.bundle_id || item.developer || "iOS Application";
  document.getElementById("modal-icon").src = item.icon || item.icon_url || "/static/default_icon.png";
  
  const statusBadge = document.getElementById("modal-status-badge");
  if (statusBadge) {
    statusBadge.innerText = "READY";
    statusBadge.style.background = "#222";
    statusBadge.style.color = "#00e676";
  }

  const terminal = document.getElementById("modal-terminal");
  const timeNow = new Date().toLocaleTimeString();
  terminal.innerText = 
`[${timeNow}] [AeroLoad Console v2.0 · Ready]
• Target Application: ${item.name} (${item.bundle_id || 'com.app'})
• Source Location:   ${item.path || item.download_url}
• Target iOS Device: ${selectedName}
• Code Signer:       Apple Developer Certificate (soliyusef@proton.me)

Click "Start Sideload" to codesign binary and push directly to device.`;

  document.getElementById("modal").style.display = "flex";
}

async function refreshSingleApp(bundleId) {
  alert(`Refreshing ${bundleId} for another 7 days...`);
  await fetch("/api/refresh-all", { method: "POST" });
  fetchRefreshStatus();
}

function setupSearch() {
  document.getElementById("search-local").addEventListener("input", (e) => {
    const q = e.target.value.toLowerCase();
    const filtered = localIpas.filter(i => i.name.toLowerCase().includes(q) || (i.bundle_id && i.bundle_id.toLowerCase().includes(q)));
    renderLocalIpas(filtered);
  });

  document.getElementById("search-library").addEventListener("input", (e) => {
    const q = e.target.value.toLowerCase();
    const filtered = libraryApps.filter(a => a.name.toLowerCase().includes(q) || a.description.toLowerCase().includes(q));
    renderLibrary(filtered);
  });

  document.getElementById("btn-rescan").addEventListener("click", fetchLocalIpas);
  document.getElementById("btn-refresh-all").addEventListener("click", async () => {
    alert("Triggering 7-day refresh for all installed apps...");
    await fetch("/api/refresh-all", { method: "POST" });
    fetchRefreshStatus();
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}


// Settings, Recent Files, and System Logs view managers
document.addEventListener("DOMContentLoaded", () => {
    initSettingsForm();
});

function initSettingsForm() {
    const form = document.getElementById("settings-form");
    const btnSave = document.getElementById("btn-save-settings");
    
    // Load Settings
    window.loadSettings = async () => {
        try {
            const res = await fetch("/settings");
            const data = await res.json();
            if (data.success) {
                const s = data.data;
                document.getElementById("set-workers").value = s.worker_count;
                document.getElementById("set-retries").value = s.retry_count;
                document.getElementById("set-search-delay").value = s.search_delay;
                document.getElementById("set-scroll-delay").value = s.scroll_delay;
                document.getElementById("set-website-timeout").value = s.website_timeout;
                document.getElementById("set-google-timeout").value = s.google_timeout;
                document.getElementById("set-checkpoint").value = s.checkpoint_interval;
                document.getElementById("set-output-dir").value = s.output_directory;
                
                document.getElementById("set-scraping").checked = s.enable_scraping;
                document.getElementById("set-translation").checked = s.enable_translation;
                document.getElementById("set-ai").checked = s.enable_ai;
                document.getElementById("set-cache").checked = s.enable_cache;
            }
        } catch (err) {
            console.error("Failed to load settings: ", err);
        }
    };

    // Save Settings
    btnSave.addEventListener("click", async () => {
        const payload = {
            worker_count: parseInt(document.getElementById("set-workers").value),
            retry_count: parseInt(document.getElementById("set-retries").value),
            search_delay: parseInt(document.getElementById("set-search-delay").value),
            scroll_delay: parseInt(document.getElementById("set-scroll-delay").value),
            website_timeout: parseInt(document.getElementById("set-website-timeout").value),
            google_timeout: parseInt(document.getElementById("set-google-timeout").value),
            checkpoint_interval: parseInt(document.getElementById("set-checkpoint").value),
            output_directory: document.getElementById("set-output-dir").value,
            enable_scraping: document.getElementById("set-scraping").checked,
            enable_translation: document.getElementById("set-translation").checked,
            enable_ai: document.getElementById("set-ai").checked,
            enable_cache: document.getElementById("set-cache").checked
        };

        try {
            const res = await fetch("/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                alert("Configurations saved successfully!");
            } else {
                alert("Failed to save configuration settings.");
            }
        } catch (err) {
            console.error("Save settings error: ", err);
        }
    });
}

// ----------------- RECENT FILES TAB -----------------
window.loadRecentFiles = async () => {
    const colMining = document.getElementById("col-mining-files");
    const colMarked = document.getElementById("col-marked-files");
    const colCleaned = document.getElementById("col-cleaned-files");
    const colProcessed = document.getElementById("col-processed-files");
    
    if (!colMining || !colMarked || !colCleaned || !colProcessed) return;
    
    colMining.innerHTML = "<div style='font-size:11px; opacity:0.5; text-align:center; padding:12px;'>Loading...</div>";
    colMarked.innerHTML = "<div style='font-size:11px; opacity:0.5; text-align:center; padding:12px;'>Loading...</div>";
    colCleaned.innerHTML = "<div style='font-size:11px; opacity:0.5; text-align:center; padding:12px;'>Loading...</div>";
    colProcessed.innerHTML = "<div style='font-size:11px; opacity:0.5; text-align:center; padding:12px;'>Loading...</div>";
    
    try {
        const res = await fetch("/history");
        const data = await res.json();
        
        colMining.innerHTML = "";
        colMarked.innerHTML = "";
        colCleaned.innerHTML = "";
        colProcessed.innerHTML = "";
        
        let counts = { mining: 0, marked: 0, cleaned: 0, processed: 0 };
        
        if (data.success && data.data.length > 0) {
            data.data.forEach(file => {
                const card = document.createElement("div");
                card.className = "file-card";
                card.style.padding = "12px";
                card.style.background = "rgba(255,255,255,0.02)";
                card.style.border = "1px solid var(--border-color)";
                card.style.borderRadius = "6px";
                card.style.display = "flex";
                card.style.flexDirection = "column";
                card.style.gap = "8px";
                
                card.innerHTML = `
                    <h5 style="margin:0; font-size:12px; font-weight:700; word-break:break-all; color:#ffffff;">${file.file_name}</h5>
                    <div style="font-size:11px; color:var(--text-secondary); display:flex; flex-direction:column; gap:4px;">
                        <div><strong>Region:</strong> ${file.district}</div>
                        <div><strong>Rows:</strong> ${file.row_count} records</div>
                        <div><strong>Size:</strong> ${file.file_size}</div>
                        <div style="font-size:10px; opacity:0.6;">${file.created_at}</div>
                    </div>
                    <div style="display:flex; gap:6px; margin-top:4px;">
                        <a href="/download/${file.file_id}" target="_blank" class="btn btn-xs btn-primary" style="flex:1; text-align:center; height:24px; display:inline-flex; align-items:center; justify-content:center; font-size:11px; font-weight:600;">Download</a>
                        <button class="btn btn-xs btn-danger btn-delete-file" data-id="${file.file_id}" style="flex:1; height:24px; display:inline-flex; align-items:center; justify-content:center; font-size:11px; font-weight:600;">Delete</button>
                    </div>
                `;
                
                if (file.category === "Mining Files") {
                    colMining.appendChild(card);
                    counts.mining++;
                } else if (file.category === "Marked Files") {
                    colMarked.appendChild(card);
                    counts.marked++;
                } else if (file.category === "Cleaned Files") {
                    colCleaned.appendChild(card);
                    counts.cleaned++;
                } else if (file.category === "Processed Files") {
                    colProcessed.appendChild(card);
                    counts.processed++;
                }
            });
            
            // Render placeholders for empty columns
            if (counts.mining === 0) colMining.innerHTML = "<div style='font-size:11px; opacity:0.4; text-align:center; padding:12px; font-style:italic;'>No files</div>";
            if (counts.marked === 0) colMarked.innerHTML = "<div style='font-size:11px; opacity:0.4; text-align:center; padding:12px; font-style:italic;'>No files</div>";
            if (counts.cleaned === 0) colCleaned.innerHTML = "<div style='font-size:11px; opacity:0.4; text-align:center; padding:12px; font-style:italic;'>No files</div>";
            if (counts.processed === 0) colProcessed.innerHTML = "<div style='font-size:11px; opacity:0.4; text-align:center; padding:12px; font-style:italic;'>No files</div>";
            
            // Map deletes
            document.querySelectorAll(".btn-delete-file").forEach(btn => {
                btn.addEventListener("click", async () => {
                    if (!confirm("Are you sure you want to delete this file permanently from disk?")) return;
                    const fileId = btn.getAttribute("data-id");
                    try {
                        const delRes = await fetch(`/history/${fileId}`, { method: "DELETE" });
                        const delData = await delRes.json();
                        if (delData.success) {
                            window.loadRecentFiles();
                        }
                    } catch (err) {
                        console.error("Delete history card error: ", err);
                    }
                });
            });
        } else {
            colMining.innerHTML = "<div style='font-size:11px; opacity:0.4; text-align:center; padding:12px; font-style:italic;'>No files</div>";
            colMarked.innerHTML = "<div style='font-size:11px; opacity:0.4; text-align:center; padding:12px; font-style:italic;'>No files</div>";
            colCleaned.innerHTML = "<div style='font-size:11px; opacity:0.4; text-align:center; padding:12px; font-style:italic;'>No files</div>";
            colProcessed.innerHTML = "<div style='font-size:11px; opacity:0.4; text-align:center; padding:12px; font-style:italic;'>No files</div>";
        }
    } catch (err) {
        console.error("Fetch history files error: ", err);
        const errMsg = "<div style='font-size:11px; color:var(--danger); text-align:center; padding:12px;'>Error</div>";
        colMining.innerHTML = errMsg;
        colMarked.innerHTML = errMsg;
        colCleaned.innerHTML = errMsg;
        colProcessed.innerHTML = errMsg;
    }
};

// ----------------- SYSTEM LOGS TAB -----------------
window.loadSystemLogs = async () => {
    const consoleBox = document.getElementById("full-system-console");
    if (!consoleBox) return;
    
    try {
        const res = await fetch("/logs");
        const data = await res.json();
        if (data.success && data.data) {
            consoleBox.innerHTML = "";
            const lines = data.data.split("\n");
            lines.forEach(line => {
                if (!line.trim()) return;
                const div = document.createElement("div");
                div.className = "terminal-line";
                
                if (line.includes("[ERROR]")) {
                    div.style.color = "#ff5630"; // Soft red for error
                } else if (line.includes("[WARNING]")) {
                    div.style.color = "#ffab00"; // Soft yellow for warning
                } else if (line.includes("[SUCCESS]")) {
                    div.style.color = "#36b37e"; // Soft green for success
                } else if (line.includes("[DEBUG]")) {
                    div.style.color = "#a855f7"; // Violet for debug
                } else if (line.includes("[INFO]")) {
                    div.style.color = "#00b8d9"; // Light blue for info
                } else {
                    div.style.color = "#919eab"; // Muted text for default system logs
                }
                
                div.textContent = line;
                consoleBox.appendChild(div);
            });
            // Auto scroll console to bottom
            consoleBox.scrollTop = consoleBox.scrollHeight;
        } else {
            consoleBox.innerHTML = "<div class='terminal-line' style='color:#919eab;'>No log data available.</div>";
        }
    } catch (err) {
        console.error("Fetch logs error: ", err);
        consoleBox.innerHTML = "<div class='terminal-line' style='color:#ff5630;'>Error reading log files.</div>";
    }
};

// Map log refreshing
const btnRefreshLogs = document.getElementById("btn-refresh-logs");
if (btnRefreshLogs) {
    btnRefreshLogs.addEventListener("click", () => {
        window.loadSystemLogs();
    });
}

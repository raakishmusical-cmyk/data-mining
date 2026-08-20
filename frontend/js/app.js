// Main SPA Application bootstrap
document.addEventListener("DOMContentLoaded", () => {
    initTabNavigation();
    initLiveClock();
    initWebSocket();
});

// Switch Dashboard views
function initTabNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    const tabPanes = document.querySelectorAll(".tab-pane");
    const pageTitle = document.getElementById("page-title");
    const pageSubtitle = document.getElementById("page-subtitle");
    
    const pageHeaders = {
        "mining": {
            title: "Mining Dashboard",
            sub: "Configure parameters and launch deep business data harvester."
        },
        "validation": {
            title: "Validation Board",
            sub: "Upload files, check duplicate clusters, and fix data classifications."
        },
        "history": {
            title: "Generated packages",
            sub: "Manage files registered in the output lead catalog."
        },
        "settings": {
            title: "Settings Manager",
            sub: "Customize execution thresholds, cache lookups, and crawler properties."
        },
        "logs": {
            title: "System Console",
            sub: "View rolling raw output messages directly from the server log file."
        }
    };

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTab = item.getAttribute("data-tab");
            
            // Clear existing log stream intervals
            if (window.logsIntervalId) {
                clearInterval(window.logsIntervalId);
                window.logsIntervalId = null;
            }
            if (window.miningLogsIntervalId) {
                clearInterval(window.miningLogsIntervalId);
                window.miningLogsIntervalId = null;
            }
            
            // Switch tabs
            navItems.forEach(nav => nav.classList.remove("active"));
            tabPanes.forEach(pane => pane.classList.remove("active"));
            
            item.classList.add("active");
            document.getElementById(`tab-${targetTab}`).classList.add("active");
            
            // Update Headers
            const headerInfo = pageHeaders[targetTab];
            if (headerInfo) {
                pageTitle.textContent = headerInfo.title;
                pageSubtitle.textContent = headerInfo.sub;
            }
            
            // Trigger specific module loads
            if (targetTab === "mining") {
                if (window.fetchAndShowMiningTerminalLogs) {
                    window.fetchAndShowMiningTerminalLogs();
                    window.miningLogsIntervalId = setInterval(window.fetchAndShowMiningTerminalLogs, 2000);
                }
            } else if (targetTab === "history") {
                if (window.loadRecentFiles) window.loadRecentFiles();
            } else if (targetTab === "settings") {
                if (window.loadSettings) window.loadSettings();
            } else if (targetTab === "logs") {
                if (window.loadSystemLogs) {
                    window.loadSystemLogs();
                    // Auto-poll every 3 seconds while viewing System Logs
                    window.logsIntervalId = setInterval(window.loadSystemLogs, 3000);
                }
            }
        });
    });
}

// Sidebar live clock
function initLiveClock() {
    const clockDisplay = document.getElementById("clock-display");
    setInterval(() => {
        const now = new Date();
        clockDisplay.textContent = now.toLocaleTimeString();
    }, 1000);
}

// WebSocket setup for real-time mining log/status streaming
let ws = null;
function initWebSocket() {
    const statusBadge = document.getElementById("status-badge");
    const wsUrl = `ws://${window.location.host}/ws/mining`;
    
    function connect() {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            statusBadge.textContent = "Online";
            statusBadge.className = "status-indicator online";
            console.log("WebSocket connected.");
        };
        
        ws.onmessage = (event) => {
            const payload = JSON.parse(event.data);
            if (payload.event === "business_saved") {
                if (window.handleBusinessSaved) {
                    window.handleBusinessSaved(payload.data);
                }
            } else {
                if (window.handleMiningStream) {
                    window.handleMiningStream(payload);
                }
            }
        };
        
        ws.onclose = () => {
            statusBadge.textContent = "Offline";
            statusBadge.className = "status-indicator offline";
            console.warn("WebSocket disconnected. Retrying in 3s...");
            setTimeout(connect, 3000);
        };
        
        ws.onerror = (err) => {
            console.error("WS error: ", err);
            ws.close();
        };
    }
    
    connect();
}

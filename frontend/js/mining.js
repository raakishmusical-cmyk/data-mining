// Lead Mining Dashboard Controller
let allLocations = {};
let currentCountry = "USA";
let selectedDistricts = new Set();
let allKeywords = [];
let selectedKeywords = new Set();
let isJobRunning = false;
let jobStartTime = null;
let consoleClearTime = null;

document.addEventListener("DOMContentLoaded", () => {
    initCustomDropdowns();
    initLocationSelectors();
    initKeywordManager();
    initMiningControls();
    checkCheckpointOnLoad();
    initLiveTableSearch();

    // Start polling logs for Mining Dashboard on load
    if (window.fetchAndShowMiningTerminalLogs) {
        window.fetchAndShowMiningTerminalLogs();
        window.miningLogsIntervalId = setInterval(window.fetchAndShowMiningTerminalLogs, 2000);
    }
});

function initCustomDropdowns() {
    // Format selector
    const formatWrapper = document.getElementById("format-select-wrapper");
    const formatTrigger = document.getElementById("format-select-trigger");
    const formatLabel = document.getElementById("format-select-label");
    const hiddenFormat = document.getElementById("input-format");

    formatTrigger.addEventListener("click", (e) => {
        e.stopPropagation();
        closeAllDropdowns(formatWrapper);
        formatWrapper.classList.toggle("open");
    });

    formatWrapper.querySelectorAll(".custom-option").forEach(opt => {
        opt.addEventListener("click", () => {
            const val = opt.getAttribute("data-value");
            hiddenFormat.value = val;
            formatLabel.textContent = opt.textContent;

            formatWrapper.querySelectorAll(".custom-option").forEach(o => o.classList.remove("selected"));
            opt.classList.add("selected");
            formatWrapper.classList.remove("open");
        });
    });

    // Workers selector
    const workersWrapper = document.getElementById("workers-select-wrapper");
    const workersTrigger = document.getElementById("workers-select-trigger");
    const workersLabel = document.getElementById("workers-select-label");
    const workersOptionsList = document.getElementById("workers-options-list");
    const hiddenWorkers = document.getElementById("input-workers");

    workersTrigger.addEventListener("click", (e) => {
        e.stopPropagation();
        closeAllDropdowns(workersWrapper);
        workersWrapper.classList.toggle("open");
    });

    const workerValues = [5, 10, 15, 20, 30, 40, 50, 60, 80, 100];
    workersOptionsList.innerHTML = "";
    workerValues.forEach(val => {
        const opt = document.createElement("div");
        opt.className = "custom-option";
        if (val === 30) opt.classList.add("selected");
        opt.setAttribute("data-value", val);
        opt.textContent = `${val} Workers`;

        opt.addEventListener("click", () => {
            hiddenWorkers.value = val;
            workersLabel.textContent = `${val} Workers`;
            workersWrapper.querySelectorAll(".custom-option").forEach(o => o.classList.remove("selected"));
            opt.classList.add("selected");
            workersWrapper.classList.remove("open");
        });
        workersOptionsList.appendChild(opt);
    });
}

// Load location data from backend/india_locations.json
// Load location data from backend/india_locations.json
async function initLocationSelectors() {
    const inputState = document.getElementById("input-state");
    const warning = document.getElementById("district-warning");
    const manualFields = document.getElementById("manual-location-fields");
    const autoFields = document.getElementById("automation-location-fields");
    const modeRadios = document.getElementsByName("district-mode");

    // Toggle automation vs manual input modes
    for (let radio of modeRadios) {
        radio.addEventListener("change", () => {
            const checkedRadio = document.querySelector('input[name="district-mode"]:checked');
            if (checkedRadio && checkedRadio.value === "manual") {
                manualFields.style.display = "block";
                autoFields.style.display = "none";
                selectedDistricts.clear();
                updateSelectedDistrictsChips();
            } else {
                manualFields.style.display = "none";
                autoFields.style.display = "block";
            }
            updateDistrictSelectedLabel();
        });
    }

    // Custom toggle click handler
    const toggleContainer = document.getElementById("district-mode-toggle");
    const toggleBg = document.getElementById("toggle-slide-bg");
    const toggleOptions = toggleContainer.querySelectorAll(".toggle-option");

    toggleOptions.forEach(opt => {
        opt.addEventListener("click", () => {
            toggleOptions.forEach(o => o.classList.remove("active"));
            opt.classList.add("active");
            const val = opt.getAttribute("data-value");

            if (val === "manual") {
                toggleBg.style.transform = "translateX(calc(100% + 6px))";
                document.querySelector('input[name="district-mode"][value="manual"]').checked = true;
                document.querySelector('input[name="district-mode"][value="manual"]').dispatchEvent(new Event("change"));
            } else {
                toggleBg.style.transform = "translateX(0)";
                document.querySelector('input[name="district-mode"][value="automation"]').checked = true;
                document.querySelector('input[name="district-mode"][value="automation"]').dispatchEvent(new Event("change"));
            }
        });
    });

    // Sync initial toggle UI state on boot
    const initialChecked = document.querySelector('input[name="district-mode"]:checked');
    if (initialChecked) {
        const activeVal = initialChecked.value;
        toggleOptions.forEach(o => {
            if (o.getAttribute("data-value") === activeVal) {
                o.classList.add("active");
            } else {
                o.classList.remove("active");
            }
        });
        if (activeVal === "manual") {
            toggleBg.style.transform = "translateX(calc(100% + 6px))";
            manualFields.style.display = "block";
            autoFields.style.display = "none";
        } else {
            toggleBg.style.transform = "translateX(0)";
            manualFields.style.display = "none";
            autoFields.style.display = "block";
        }
    }

    // Custom State Select Toggle
    const stateWrapper = document.getElementById("state-select-wrapper");
    const stateTrigger = document.getElementById("state-select-trigger");
    const stateSearchInput = document.getElementById("state-search-input");

    stateTrigger.addEventListener("click", (e) => {
        e.stopPropagation();
        closeAllDropdowns(stateWrapper);
        stateWrapper.classList.toggle("open");
        if (stateWrapper.classList.contains("open")) {
            stateSearchInput.focus();
        }
    });

    // Custom Country Select Toggle
    const countryWrapper = document.getElementById("country-select-wrapper");
    const countryTrigger = document.getElementById("country-select-trigger");

    countryTrigger.addEventListener("click", (e) => {
        e.stopPropagation();
        closeAllDropdowns(countryWrapper);
        countryWrapper.classList.toggle("open");
    });

    const countryOptions = countryWrapper.querySelectorAll(".custom-option");
    countryOptions.forEach(opt => {
        opt.addEventListener("click", () => {
            countryOptions.forEach(o => o.classList.remove("selected"));
            opt.classList.add("selected");
            const val = opt.getAttribute("data-value");
            document.getElementById("country-select-label").textContent = val;
            document.getElementById("input-country").value = val;
            countryWrapper.classList.remove("open");
            handleCountryChange(val);
        });
    });

    stateSearchInput.addEventListener("input", () => {
        filterStateOptions();
    });

    try {
        const res = await fetch("/locations");
        const json = await res.json();
        if (json.success) {
            allLocations = json.data;
            handleCountryChange("USA");
        }
    } catch (err) {
        console.error("Failed to load locations catalog:", err);
    }

    // Populate districts checklist when state selection changes
    inputState.addEventListener("change", () => {
        selectedDistricts.clear();
        warning.style.display = "none";
        renderDistrictList();
        updateSelectedDistrictsChips();
        updateDistrictSelectedLabel();
    });

    // Custom District select Toggle
    const distWrapper = document.getElementById("district-select-wrapper");
    const distTrigger = document.getElementById("district-select-trigger");
    const distSearchInput = document.getElementById("district-search-input");

    distTrigger.addEventListener("click", (e) => {
        e.stopPropagation();
        closeAllDropdowns(distWrapper);
        distWrapper.classList.toggle("open");
        if (distWrapper.classList.contains("open")) {
            distSearchInput.focus();
        }
    });

    distSearchInput.addEventListener("input", () => {
        renderDistrictList();
    });

    document.addEventListener("click", () => {
        closeAllDropdowns();
    });
}

function closeAllDropdowns(exceptWrapper = null) {
    document.querySelectorAll(".custom-select-wrapper").forEach(w => {
        if (w !== exceptWrapper) {
            w.classList.remove("open");
        }
    });
}

function selectStateCustom(stateName) {
    const inputState = document.getElementById("input-state");
    const label = document.getElementById("state-select-label");
    const wrapper = document.getElementById("state-select-wrapper");

    inputState.value = stateName;
    label.textContent = stateName;

    wrapper.querySelectorAll(".custom-option").forEach(opt => {
        if (opt.getAttribute("data-value") === stateName) {
            opt.classList.add("selected");
        } else {
            opt.classList.remove("selected");
        }
    });

    inputState.dispatchEvent(new Event("change"));
    wrapper.classList.remove("open");
}

function filterStateOptions() {
    const searchVal = document.getElementById("state-search-input").value.toLowerCase();
    const options = document.querySelectorAll("#state-options-list .custom-option");
    options.forEach(opt => {
        const text = opt.textContent.toLowerCase();
        opt.style.display = text.includes(searchVal) ? "flex" : "none";
    });
}

function handleCountryChange(country) {
    currentCountry = country;
    selectedDistricts.clear();
    updateSelectedDistrictsChips();
    updateDistrictSelectedLabel();

    const inputState = document.getElementById("input-state");
    const stateLabel = document.getElementById("state-select-label");
    const warning = document.getElementById("district-warning");
    if (warning) warning.style.display = "none";

    inputState.value = "";

    const lblStateSelect = document.getElementById("lbl-state-select");
    const lblDistrictSelectTitle = document.getElementById("lbl-district-select-title");
    const stateSearchInput = document.getElementById("state-search-input");
    const districtSearchInput = document.getElementById("district-search-input");

    if (country === "USA") {
        if (lblStateSelect) lblStateSelect.textContent = "State";
        if (stateLabel) stateLabel.textContent = "Select State";
        if (lblDistrictSelectTitle) lblDistrictSelectTitle.textContent = "Select Cities";
        document.getElementById("district-chips-display").textContent = "Select Cities";
        if (stateSearchInput) stateSearchInput.placeholder = "Search state (e.g. Texas)...";
        if (districtSearchInput) districtSearchInput.placeholder = "Search city...";
    } else {
        if (lblStateSelect) lblStateSelect.textContent = "Province";
        if (stateLabel) stateLabel.textContent = "Select Province";
        if (lblDistrictSelectTitle) lblDistrictSelectTitle.textContent = "Select Districts";
        document.getElementById("district-chips-display").textContent = "Select Districts";
        if (stateSearchInput) stateSearchInput.placeholder = "Search province (e.g. Bagmati)...";
        if (districtSearchInput) districtSearchInput.placeholder = "Search district...";
    }

    inputState.innerHTML = `<option value="">Select ${country === "USA" ? "State" : "Province"}</option>`;
    const stateOptionsList = document.getElementById("state-options-list");
    stateOptionsList.innerHTML = "";

    const countryData = allLocations[country];
    if (countryData && countryData.states) {
        countryData.states.forEach(s => {
            const optNative = document.createElement("option");
            optNative.value = s.state;
            optNative.textContent = s.state;
            inputState.appendChild(optNative);

            const optCustom = document.createElement("div");
            optCustom.className = "custom-option";
            optCustom.setAttribute("data-value", s.state);
            optCustom.textContent = `${s.state} (${s.sid})`;

            optCustom.addEventListener("click", () => {
                selectStateCustom(s.state);
            });
            stateOptionsList.appendChild(optCustom);
        });
    }

    renderDistrictList();
}

function renderDistrictList() {
    const stateVal = document.getElementById("input-state").value;
    const optionsList = document.getElementById("district-options-list");
    const searchVal = document.getElementById("district-search-input").value.toLowerCase();
    const warning = document.getElementById("district-warning");

    if (!stateVal) {
        const itemType = currentCountry === "USA" ? "State" : "Province";
        optionsList.innerHTML = `<div style="text-align: center; padding: 20px 0; opacity: 0.6; font-size: 13px;">Please select a ${itemType} first.</div>`;
        return;
    }

    const countryData = allLocations[currentCountry];
    if (!countryData || !countryData.states) return;

    const stateObj = countryData.states.find(s => s.state === stateVal);
    if (!stateObj) return;

    optionsList.innerHTML = "";
    const filtered = stateObj.districts.filter(d => d.toLowerCase().includes(searchVal));

    if (filtered.length === 0) {
        const itemTypePlural = currentCountry === "USA" ? "cities" : "districts";
        optionsList.innerHTML = `<div style="text-align: center; padding: 15px 0; opacity: 0.6; font-size: 12px;">No matching ${itemTypePlural}.</div>`;
        return;
    }

    filtered.forEach(dist => {
        const row = document.createElement("label");
        row.className = "custom-option-checkbox";

        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.value = dist;
        cb.checked = selectedDistricts.has(dist);

        cb.addEventListener("change", (e) => {
            if (e.target.checked) {
                if (selectedDistricts.size >= 10) {
                    e.target.checked = false;
                    warning.style.display = "block";
                    setTimeout(() => warning.style.display = "none", 4000);
                    return;
                }
                selectedDistricts.add(dist);
            } else {
                selectedDistricts.delete(dist);
                warning.style.display = "none";
            }
            updateSelectedDistrictsChips();
            updateDistrictSelectedLabel();
        });

        row.appendChild(cb);
        row.appendChild(document.createTextNode(dist));
        optionsList.appendChild(row);
    });
}

function updateSelectedDistrictsChips() {
    const chipsDisplay = document.getElementById("district-chips-display");
    const chipsContainer = document.getElementById("selected-districts-chips");
    chipsDisplay.innerHTML = "";
    chipsContainer.innerHTML = "";

    if (selectedDistricts.size === 0) {
        chipsDisplay.textContent = currentCountry === "USA" ? "Select Cities" : "Select Districts";
        return;
    }

    selectedDistricts.forEach(dist => {
        const chip = document.createElement("div");
        chip.className = "trigger-chip";
        chip.textContent = dist;

        const close = document.createElement("span");
        close.className = "close-chip";
        close.textContent = "×";
        close.addEventListener("click", (e) => {
            e.stopPropagation();
            selectedDistricts.delete(dist);
            renderDistrictList();
            updateSelectedDistrictsChips();
            updateDistrictSelectedLabel();
        });

        chip.appendChild(close);
        chipsDisplay.appendChild(chip);

        // Populate selected-districts-chips hidden container to replicate manual list logic
        const shadowChip = chip.cloneNode(true);
        shadowChip.querySelector(".close-chip").addEventListener("click", (ev) => {
            ev.stopPropagation();
            selectedDistricts.delete(dist);
            renderDistrictList();
            updateSelectedDistrictsChips();
            updateDistrictSelectedLabel();
        });
        chipsContainer.appendChild(shadowChip);
    });
}

function updateDistrictSelectedLabel() {
    const lbl = document.getElementById("lbl-districts-selected-count");
    if (lbl) {
        lbl.textContent = `${selectedDistricts.size} Selected`;
    }
}

// Keyword chip management actions
async function initKeywordManager() {
    const kwSearch = document.getElementById("kw-search");
    const btnSelectAll = document.getElementById("btn-kw-select-all");
    const btnDeselectAll = document.getElementById("btn-kw-deselect-all");
    const btnAddCustom = document.getElementById("btn-add-custom-kw");
    const inputCustom = document.getElementById("input-custom-keyword");

    await loadKeywords();

    kwSearch.addEventListener("input", () => {
        filterKeywordChips();
    });

    btnSelectAll.addEventListener("click", () => {
        allKeywords.forEach(k => selectedKeywords.add(k.keyword));
        renderKeywordChips();
        updateKeywordSelectedCounter();
    });

    btnDeselectAll.addEventListener("click", () => {
        selectedKeywords.clear();
        renderKeywordChips();
        updateKeywordSelectedCounter();
    });

    btnAddCustom.addEventListener("click", async () => {
        const word = inputCustom.value.trim();
        if (!word) return;
        try {
            const res = await fetch("/keywords", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ keyword: word })
            });
            const data = await res.json();
            if (data.success) {
                inputCustom.value = "";
                await loadKeywords();
                // Select newly added keyword automatically
                selectedKeywords.add(word);
                renderKeywordChips();
                updateKeywordSelectedCounter();
            } else {
                alert(data.detail || "Keyword already exists.");
            }
        } catch (err) {
            console.error("Failed to append custom keyword:", err);
        }
    });

    inputCustom.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            btnAddCustom.click();
        }
    });
}

async function loadKeywords() {
    try {
        const res = await fetch("/keywords");
        const json = await res.json();
        if (json.success) {
            allKeywords = json.data;
            renderKeywordChips();
            updateKeywordSelectedCounter();
        }
    } catch (err) {
        console.error("Failed to query keywords:", err);
    }
}

function renderKeywordChips() {
    const wrapper = document.getElementById("keyword-chips-wrapper");
    wrapper.innerHTML = "";

    allKeywords.forEach(kwObj => {
        const chip = document.createElement("div");
        chip.className = "kw-chip";
        if (selectedKeywords.has(kwObj.keyword)) {
            chip.classList.add("selected");
        }
        if (!kwObj.is_default) {
            chip.classList.add("custom-kw");
        }

        const label = document.createElement("span");
        label.textContent = kwObj.keyword;
        label.addEventListener("click", () => {
            if (selectedKeywords.has(kwObj.keyword)) {
                selectedKeywords.delete(kwObj.keyword);
                chip.classList.remove("selected");
            } else {
                selectedKeywords.add(kwObj.keyword);
                chip.classList.add("selected");
            }
            updateKeywordSelectedCounter();
        });
        chip.appendChild(label);

        // Delete button for custom keywords
        if (!kwObj.is_default) {
            const del = document.createElement("span");
            del.className = "btn-delete-kw";
            del.textContent = "×";
            del.title = "Delete keyword";
            del.addEventListener("click", async (e) => {
                e.stopPropagation();
                if (!confirm(`Remove custom keyword "${kwObj.keyword}"?`)) return;
                try {
                    const res = await fetch(`/keywords/${kwObj.id}`, { method: "DELETE" });
                    const data = await res.json();
                    if (data.success) {
                        selectedKeywords.delete(kwObj.keyword);
                        await loadKeywords();
                    }
                } catch (err) {
                    console.error("Delete keyword failure:", err);
                }
            });
            chip.appendChild(del);
        }

        wrapper.appendChild(chip);
    });
}

function filterKeywordChips() {
    const searchVal = document.getElementById("kw-search").value.toLowerCase();
    const chips = document.querySelectorAll("#keyword-chips-wrapper .kw-chip");
    chips.forEach(chip => {
        const text = chip.querySelector("span").textContent.toLowerCase();
        if (text.includes(searchVal)) {
            chip.style.display = "flex";
        } else {
            chip.style.display = "none";
        }
    });
}

function updateKeywordSelectedCounter() {
    const lbl = document.getElementById("lbl-keyword-counter");
    if (lbl) {
        lbl.textContent = `${selectedKeywords.size} Selected`;
    }
}

// Mining start/pause/resume/stop event actions
function initMiningControls() {
    const btnStart = document.getElementById("btn-start-mining");
    const btnPause = document.getElementById("btn-pause-mining");
    const btnResume = document.getElementById("btn-resume-mining");
    const btnStop = document.getElementById("btn-stop-mining");
    const btnClearLogs = document.getElementById("btn-clear-logs");

    btnStart.addEventListener("click", async () => {
        // Collect districts
        let districts = [];
        const mode = document.querySelector('input[name="district-mode"]:checked').value;
        let stateVal = "";

        if (mode === "manual") {
            const manualText = document.getElementById("input-districts-manual").value;
            districts = manualText.split(/[\n,]+/).map(d => d.trim()).filter(d => d);
            stateVal = "Manual"; // Manual mode placeholder
            if (districts.length > 10) {
                alert("Maximum 10 locations allowed in Manual mode. Trimming list to first 10.");
                districts = districts.slice(0, 10);
                document.getElementById("input-districts-manual").value = districts.join("\n");
            }
        } else {
            stateVal = document.getElementById("input-state").value;
            districts = Array.from(selectedDistricts);
            if (!stateVal) {
                alert(`Please select a ${currentCountry === "USA" ? "State" : "Province"} first.`);
                return;
            }
        }

        if (districts.length === 0) {
            alert("Please select or type at least one target location.");
            return;
        }

        const keywords = Array.from(selectedKeywords);
        if (keywords.length === 0) {
            alert("Please select at least one keyword chip.");
            return;
        }

        const format = document.getElementById("input-format").value;
        btnStart.disabled = true;

        try {
            // Save settings workers count if updated
            const workersCount = parseInt(document.getElementById("input-workers").value) || 30;
            await fetch("/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ worker_count: workersCount })
            });

            // Start Job
            const translateVal = document.getElementById("chk-translate-english") ? document.getElementById("chk-translate-english").checked : true;
            const res = await fetch("/mining/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ country: currentCountry, state: stateVal, districts, keywords, format, translate_to_english: translateVal })
            });
            const data = await res.json();
            if (data.success) {
                btnPause.disabled = false;
                btnStop.disabled = false;
                btnStart.disabled = true;
                btnResume.style.display = "none";
                // Clear live leads table on new start
                clearLiveLeadsTable();
                isJobRunning = true;
                jobStartTime = new Date();
                consoleClearTime = null; // reset console clear history
            } else {
                alert(data.message || "Failed to start mining.");
                btnStart.disabled = false;
            }
        } catch (err) {
            console.error("Mining Start Failed: ", err);
            btnStart.disabled = false;
        }
    });

    btnPause.addEventListener("click", async () => {
        try {
            const res = await fetch("/mining/pause", { method: "POST" });
            const data = await res.json();
            if (data.success) {
                btnPause.style.display = "none";
                btnResume.style.display = "inline-flex";
                btnResume.disabled = false;
            }
        } catch (err) {
            console.error("Pause job failure:", err);
        }
    });

    btnResume.addEventListener("click", async () => {
        try {
            const res = await fetch("/mining/resume", { method: "POST" });
            const data = await res.json();
            if (data.success) {
                btnResume.style.display = "none";
                btnPause.style.display = "inline-flex";
                btnPause.disabled = false;
                btnStop.disabled = false;
                btnStart.disabled = true;
                isJobRunning = true;
                if (!jobStartTime) jobStartTime = new Date();
                consoleClearTime = null; // reset console clear history
            } else {
                alert(data.message || "Failed to resume mining.");
            }
        } catch (err) {
            console.error("Resume job failure:", err);
        }
    });

    btnStop.addEventListener("click", async () => {
        if (!confirm("Are you sure you want to stop mining? Current progress will compile to history.")) return;
        try {
            const res = await fetch("/mining/stop", { method: "POST" });
            const data = await res.json();
            if (data.success) {
                resetControlButtons();
                isJobRunning = false;
                jobStartTime = null;
            }
        } catch (err) {
            console.error("Stop job failure:", err);
        }
    });

    btnClearLogs.addEventListener("click", () => {
        document.getElementById("live-terminal").innerHTML = "";
        consoleClearTime = new Date();
    });

    const btnCopyLogs = document.getElementById("btn-copy-logs");
    if (btnCopyLogs) {
        btnCopyLogs.addEventListener("click", () => {
            const terminalText = Array.from(document.querySelectorAll("#live-terminal .terminal-line"))
                .map(line => line.textContent)
                .join("\n");
            navigator.clipboard.writeText(terminalText);

            const originalText = btnCopyLogs.textContent;
            btnCopyLogs.textContent = "Copied!";
            setTimeout(() => {
                btnCopyLogs.textContent = originalText;
            }, 2000);
        });
    }
}

function resetControlButtons() {
    document.getElementById("btn-start-mining").disabled = false;
    document.getElementById("btn-pause-mining").disabled = true;
    document.getElementById("btn-pause-mining").style.display = "inline-flex";
    document.getElementById("btn-resume-mining").style.display = "none";
    document.getElementById("btn-stop-mining").disabled = true;
}

// Check if checkpoint file exists in SQLite DB on dashboard boot
async function checkCheckpointOnLoad() {
    try {
        const res = await fetch("/mining/checkpoint");
        const json = await res.json();
        if (json.success && json.data && json.data.job_id) {
            const btnResume = document.getElementById("btn-resume-mining");
            btnResume.style.display = "inline-flex";
            btnResume.disabled = false;

            // Console notice
            const term = document.getElementById("live-terminal");
            const div = document.createElement("div");
            div.className = "terminal-line warning";
            div.textContent = `[SYSTEM] Found crash or paused checkpoint for job ID: ${json.data.job_id.substring(0, 8)}. You can click "Resume" to continue harvesting.`;
            term.appendChild(div);
        }
    } catch (err) {
        console.error("Failed to poll sqlite checkpoints status:", err);
    }
}

// Prepends real-time leads record rows to live tables
window.handleBusinessSaved = function (record) {
    const tbody = document.querySelector("#live-leads-table tbody");

    // Remove placeholder empty row if exists
    const placeholder = tbody.querySelector(".empty-row-placeholder");
    if (placeholder) {
        placeholder.remove();
    }

    const row = document.createElement("tr");
    row.className = "flash-row";

    // Set row cells
    row.innerHTML = `
        <td style="padding: 10px; border-bottom: 1px solid var(--border); font-weight:600;">${record.name}</td>
        <td style="padding: 10px; border-bottom: 1px solid var(--border); font-family: monospace;">${record.phone}</td>
        <td style="padding: 10px; border-bottom: 1px solid var(--border);">${record.email}</td>
        <td style="padding: 10px; border-bottom: 1px solid var(--border); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:180px;"><a href="${record.website}" target="_blank" style="color:var(--primary);">${record.website}</a></td>
        <td style="padding: 10px; border-bottom: 1px solid var(--border); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:120px;">${record.street}</td>
        <td style="padding: 10px; border-bottom: 1px solid var(--border);">${record.city}</td>
        <td style="padding: 10px; border-bottom: 1px solid var(--border);">${record.state}</td>
        <td style="padding: 10px; border-bottom: 1px solid var(--border);">${record.country}</td>
        <td style="padding: 10px; border-bottom: 1px solid var(--border);"><span class="badge" style="background:var(--success-bg); color:var(--success);">${record.industry}</span></td>
        <td style="padding: 10px; border-bottom: 1px solid var(--border);"><span class="badge" style="background:var(--warning-bg); color:var(--warning);">${record.tags}</span></td>
        <td style="padding: 10px; border-bottom: 1px solid var(--border); font-weight:700; color:var(--success);">${record.status}</td>
    `;

    tbody.insertBefore(row, tbody.firstChild);

    // Limit live record rows to prevent DOM bloat
    if (tbody.children.length > 500) {
        tbody.lastChild.remove();
    }

    // Update count badge
    const badge = document.getElementById("lbl-live-leads-counter");
    const count = tbody.children.length;
    badge.textContent = `${count} Leads Mined`;
};

function clearLiveLeadsTable() {
    const tbody = document.querySelector("#live-leads-table tbody");
    tbody.innerHTML = '<tr class="empty-row-placeholder"><td colspan="11" style="text-align:center; padding:30px; opacity:0.5; font-style:italic;">No records mined in the current session. Run a job to see leads stream here.</td></tr>';
    document.getElementById("lbl-live-leads-counter").textContent = "0 Leads Mined";
}

function initLiveTableSearch() {
    const input = document.getElementById("live-leads-search");
    input.addEventListener("input", () => {
        const query = input.value.toLowerCase();
        const rows = document.querySelectorAll("#live-leads-table tbody tr:not(.empty-row-placeholder)");
        rows.forEach(row => {
            const cells = Array.from(row.querySelectorAll("td"));
            const match = cells.some(cell => cell.textContent.toLowerCase().includes(query));
            row.style.display = match ? "" : "none";
        });
    });
}

// Websocket callback mapped from app.js
window.handleMiningStream = function (payload) {
    const { status, current_state, current_district, current_keyword, current_business, current_worker, current_stage, elapsed_time, progress, stats, logs } = payload;

    // Update Control Buttons depending on job status
    const btnStart = document.getElementById("btn-start-mining");
    const btnPause = document.getElementById("btn-pause-mining");
    const btnResume = document.getElementById("btn-resume-mining");
    const btnStop = document.getElementById("btn-stop-mining");

    if (status === "Running" || status === "Paused") {
        btnStart.disabled = true;
        btnStop.disabled = false;
        if (status === "Paused") {
            btnPause.style.display = "none";
            btnResume.style.display = "inline-flex";
            btnResume.disabled = false;
        } else {
            btnPause.style.display = "inline-flex";
            btnPause.disabled = false;
            btnResume.style.display = "none";
        }
    } else {
        resetControlButtons();
        // Hide resume if job completes/stops
        btnResume.style.display = "none";
    }

    if (status === "Running") {
        isJobRunning = true;
        if (!jobStartTime) {
            jobStartTime = new Date(Date.now() - (elapsed_time || 0) * 1000);
        }
    }

    if (status === "Completed") {
        if (isJobRunning) {
            isJobRunning = false;
            setTimeout(() => {
                showCompletionPopup(payload, false);
            }, 1000);
        }
    } else if (status === "Stopped") {
        if (isJobRunning) {
            isJobRunning = false;
            setTimeout(() => {
                showCompletionPopup(payload, true);
            }, 1000);
        }
    } else if (status === "Failed") {
        isJobRunning = false;
        jobStartTime = null;
    }

    // Update Activity Displays
    document.getElementById("act-state").textContent = current_state || "N/A";
    document.getElementById("act-district").textContent = current_district || "N/A";
    document.getElementById("act-keyword").textContent = current_keyword || "N/A";
    document.getElementById("act-website").textContent = (current_worker === "Website Worker" && current_business) ? current_business : "N/A";
    document.getElementById("act-business").textContent = current_business || "N/A";

    const stageBadge = document.getElementById("act-stage");
    if (stageBadge) {
        if (status === "Stopping") {
            stageBadge.textContent = "Stopping Mining... While workers finish";
            stageBadge.style.background = "rgba(255,171,0,0.1)";
            stageBadge.style.color = "var(--warning)";
        } else if (status === "Stopped") {
            stageBadge.textContent = "Mining Stopped Successfully";
            stageBadge.style.background = "rgba(54,179,126,0.1)";
            stageBadge.style.color = "var(--success)";
        } else {
            stageBadge.textContent = current_stage || "Idle";
            if (current_stage === "Website Scraping" || current_stage === "Email Extraction") {
                stageBadge.style.background = "rgba(255,171,0,0.1)";
                stageBadge.style.color = "var(--warning)";
            } else if (current_stage === "Classification" || current_stage === "Saving Excel") {
                stageBadge.style.background = "rgba(32,101,209,0.1)";
                stageBadge.style.color = "var(--primary)";
            } else if (current_stage === "Completed") {
                stageBadge.style.background = "rgba(54,179,126,0.1)";
                stageBadge.style.color = "var(--success)";
            } else {
                stageBadge.style.background = "rgba(255,171,0,0.1)";
                stageBadge.style.color = "var(--warning)";
            }
        }
    }

    const stageText = document.getElementById("act-stage-text");
    if (stageText) {
        if (status === "Stopping") {
            stageText.textContent = "Stopping Mining... While workers finish";
            stageText.style.color = "#ffab00";
        } else if (status === "Stopped") {
            stageText.textContent = "Mining Stopped Successfully";
            stageText.style.color = "#10b981";
        } else {
            stageText.textContent = current_stage || "Idle";
            if (current_stage === "Website Scraping" || current_stage === "Email Extraction") {
                stageText.style.color = "#ffab00";
            } else if (current_stage === "Classification" || current_stage === "Saving Excel") {
                stageText.style.color = "#3b82f6";
            } else if (current_stage === "Completed") {
                stageText.style.color = "#10b981";
            } else {
                stageText.style.color = "#ffab00";
            }
        }
    }

    // Update Progress Bars Fills and labels
    if (progress) {
        const parseCount = (str) => {
            if (!str) return { current: 0, total: 0 };
            const parts = str.split("/");
            return {
                current: parseInt(parts[0]) || 0,
                total: parseInt(parts[1]) || 0
            };
        };

        const distData = parseCount(progress.district_count);
        const kwData = parseCount(progress.keyword_count);
        const busData = parseCount(progress.business_count);

        const totalDists = distData.total || 1;
        const totalKws = kwData.total || 1;
        const completedDists = Math.max(0, distData.current - 1);
        const completedKws = Math.max(0, kwData.current - 1);

        const overallCompleted = (completedDists * totalKws) + completedKws;
        const overallTotal = totalDists * totalKws;
        const overallRemaining = Math.max(0, overallTotal - overallCompleted);

        document.getElementById("overall-progress-fill").style.width = `${progress.overall}%`;
        document.getElementById("lbl-overall-progress-count").textContent =
            `${progress.overall}% (Completed: ${overallCompleted}, Remaining: ${overallRemaining})`;

        document.getElementById("district-progress-fill").style.width = `${progress.district}%`;
        document.getElementById("lbl-district-progress-count").textContent =
            `${progress.district}% (Completed: ${completedDists}, Remaining: ${totalDists - completedDists})`;

        document.getElementById("keyword-progress-fill").style.width = `${progress.keyword}%`;
        document.getElementById("lbl-keyword-progress-count").textContent =
            `${progress.keyword}% (Completed: ${completedKws}, Remaining: ${totalKws - completedKws})`;

        document.getElementById("business-progress-fill").style.width = `${progress.business}%`;
        const completedBus = busData.current;
        const totalBus = busData.total;
        const remainingBus = Math.max(0, totalBus - completedBus);
        document.getElementById("lbl-business-progress-count").textContent =
            `${progress.business}% (Completed: ${completedBus}, Remaining: ${remainingBus})`;
    }

    // Update Stats Card Counters
    document.getElementById("stat-found").textContent = stats.businesses_found;
    document.getElementById("stat-saved").textContent = stats.businesses_saved;
    document.getElementById("stat-phones").textContent = parseInt(stats.phone_count) + parseInt(stats.mobile_count);
    document.getElementById("stat-emails").textContent = stats.email_count;
    document.getElementById("stat-websites").textContent = stats.website_count;
    document.getElementById("stat-skipped").textContent = stats.duplicates_skipped;

    // Failed Leads count
    const failedElem = document.getElementById("stat-failed-leads");
    if (failedElem) {
        failedElem.textContent = stats.error_count || 0;
    }

    // Retry Count
    const retryElem = document.getElementById("stat-retry-count");
    if (retryElem) {
        retryElem.textContent = stats.retry_count || 0;
    }

    // Success Rate
    const successRateElem = document.getElementById("stat-success-rate");
    if (successRateElem) {
        const found = parseInt(stats.businesses_found) || 0;
        const saved = parseInt(stats.businesses_saved) || 0;
        const rateVal = found > 0 ? Math.round((saved / found) * 100) : 100;
        successRateElem.textContent = `${rateVal}%`;
    }

    // CPU and Memory dynamic fluctuation simulator
    const cpuElem = document.getElementById("stat-cpu");
    const memElem = document.getElementById("stat-memory");
    if (status === "Running") {
        if (cpuElem) cpuElem.textContent = (4.8 + Math.random() * 8.5).toFixed(1) + "%";
        if (memElem) memElem.textContent = (180 + Math.floor(Math.random() * 16)).toFixed(0) + " MB";
    } else {
        if (cpuElem) cpuElem.textContent = "0.0%";
        if (memElem) memElem.textContent = "15 MB";
    }

    // CSV Output Size estimation
    const csvSizeElem = document.getElementById("stat-csv-size");
    if (csvSizeElem) {
        const savedCount = parseInt(stats.businesses_saved) || 0;
        const sizeVal = savedCount > 0 ? (savedCount * 0.25).toFixed(1) : "0.0";
        csvSizeElem.textContent = `${sizeVal} KB`;
    }

    // Workers Count Display
    document.getElementById("header-worker-count").textContent = (status === "Running") ? "30" : "0";

    // Businesses Per Second calculation
    const currentSpeed = (elapsed_time > 0) ? (stats.businesses_saved / elapsed_time).toFixed(2) : "0.0";
    document.getElementById("stat-bps").textContent = currentSpeed;

    // Queue Size
    const totalDistricts = document.getElementById("input-state").value ? selectedDistricts.size : 1;
    const totalKeywords = selectedKeywords.size || 1;
    document.getElementById("stat-queue-size").textContent = Math.max(0, (totalDistricts * totalKeywords) - (progress ? parseInt(progress.district_count.split("/")[0]) : 0));

    // Elapsed Time String formatting (HH:MM:SS)
    const hours = String(Math.floor(elapsed_time / 3600)).padStart(2, '0');
    const minutes = String(Math.floor((elapsed_time % 3600) / 60)).padStart(2, '0');
    const seconds = String(elapsed_time % 60).padStart(2, '0');
    document.getElementById("stat-elapsed-time").textContent = `${hours}:${minutes}:${seconds}`;

    // ETA Predictor (Assume speed-based estimation)
    if (status === "Running" && parseFloat(currentSpeed) > 0) {
        const remainingQueueItems = Math.max(0, (stats.businesses_found - stats.businesses_saved));
        const etaSecs = remainingQueueItems / parseFloat(currentSpeed);
        if (etaSecs > 0) {
            const etaMins = Math.ceil(etaSecs / 60);
            document.getElementById("stat-eta").textContent = `~${etaMins} mins`;
        } else {
            document.getElementById("stat-eta").textContent = "N/A";
        }
    } else {
        document.getElementById("stat-eta").textContent = "N/A";
    }

    // Refresh terminal logs from Output/Logs/app.log
    if (window.fetchAndShowMiningTerminalLogs) {
        window.fetchAndShowMiningTerminalLogs();
    }
};

async function showCompletionPopup(payload, isStopped = false) {
    const modal = document.getElementById("completion-modal");
    if (!modal) return;

    const titleElem = document.getElementById("pop-title");
    const descElem = document.getElementById("pop-desc");
    const iconCircle = document.getElementById("pop-icon-circle");
    const iconSymbol = document.getElementById("pop-icon-symbol");

    if (isStopped) {
        if (titleElem) titleElem.textContent = "Mining Stopped";
        if (descElem) descElem.textContent = "Mining has been stopped successfully. All mined data up to this point has been safely saved.";
        if (iconCircle) {
            iconCircle.style.background = "rgba(255,171,0,0.1)";
            iconCircle.style.borderColor = "#ffab00";
            iconCircle.style.boxShadow = "0 0 20px rgba(255,171,0,0.25)";
        }
        if (iconSymbol) {
            iconSymbol.textContent = "✓";
            iconSymbol.style.color = "#ffab00";
        }
    } else {
        if (titleElem) titleElem.textContent = "Mining Completed Successfully!";
        if (descElem) descElem.textContent = "Lead harvesting and website enrichment pipeline has completed.";
        if (iconCircle) {
            iconCircle.style.background = "rgba(16,185,129,0.1)";
            iconCircle.style.borderColor = "#10b981";
            iconCircle.style.boxShadow = "0 0 20px rgba(16,185,129,0.25)";
        }
        if (iconSymbol) {
            iconSymbol.textContent = "✓";
            iconSymbol.style.color = "#10b981";
        }
    }

    // Fill metrics
    const found = payload.stats.businesses_found || 0;
    const saved = payload.stats.businesses_saved || 0;
    const skipped = payload.stats.duplicates_skipped || 0;
    const failed = payload.stats.error_count || 0;

    const email_count = payload.stats.email_count || 0;
    const phone_count = payload.stats.phone_count || 0;
    const website_count = payload.stats.website_count || 0;

    const instagram_count = payload.stats.instagram_count || 0;
    const facebook_count = payload.stats.facebook_count || 0;
    const linkedin_count = payload.stats.linkedin_count || 0;
    const twitter_count = payload.stats.twitter_count || 0;
    const youtube_count = payload.stats.youtube_count || 0;

    document.getElementById("pop-found").textContent = found;
    document.getElementById("pop-saved").textContent = saved;
    document.getElementById("pop-skipped").textContent = skipped;
    document.getElementById("pop-failed").textContent = failed;

    document.getElementById("pop-emails").textContent = email_count;
    document.getElementById("pop-phones").textContent = phone_count;
    document.getElementById("pop-websites").textContent = website_count;

    document.getElementById("pop-instagram").textContent = instagram_count;
    document.getElementById("pop-facebook").textContent = facebook_count;
    document.getElementById("pop-linkedin").textContent = linkedin_count;
    document.getElementById("pop-twitter-yt").textContent = twitter_count + youtube_count;

    // Elapsed time formatting
    const elapsed = payload.stats.elapsed_time || payload.elapsed_time || 0;
    const hours = String(Math.floor(elapsed / 3600)).padStart(2, '0');
    const minutes = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0');
    const seconds = String(elapsed % 60).padStart(2, '0');
    document.getElementById("pop-duration").textContent = `${hours}:${minutes}:${seconds}`;

    // Enrichment quality score
    const completeness = saved > 0 ? Math.min(100, Math.round(((email_count + phone_count + website_count) / (saved * 3)) * 100)) : 100;
    document.getElementById("pop-quality-percentage").textContent = `Completeness: ${completeness}%`;
    const starsCount = completeness >= 90 ? 5 : (completeness >= 70 ? 4 : (completeness >= 50 ? 3 : (completeness >= 30 ? 2 : 1)));
    const popStars = document.querySelector("#completion-modal div[style*='color:#ffab00']");
    if (popStars) {
        popStars.innerHTML = "★".repeat(starsCount) + "☆".repeat(5 - starsCount);
    }

    // Data cleanliness
    const cleanlinessErrors = document.getElementById("pop-cleanliness-errors");
    if (cleanlinessErrors) {
        cleanlinessErrors.textContent = `${failed} Errors`;
        cleanlinessErrors.style.color = failed > 0 ? "#ff5630" : "#36b37e";
    }
    const cleanlinessMissing = document.getElementById("pop-cleanliness-missing");
    if (cleanlinessMissing) {
        const missingEmails = Math.max(0, saved - email_count);
        const missingWebsites = Math.max(0, saved - website_count);
        cleanlinessMissing.textContent = `Missing: E: ${missingEmails} | W: ${missingWebsites}`;
    }

    // Determine target districts
    const mode = document.querySelector('input[name="district-mode"]:checked').value;
    let targetDistricts = [];
    if (mode === "manual") {
        const text = document.getElementById("input-districts-manual").value;
        targetDistricts = text.split(/[\n,]+/).map(d => d.trim()).filter(d => d);
        if (targetDistricts.length > 10) targetDistricts = targetDistricts.slice(0, 10);
    } else {
        targetDistricts = Array.from(selectedDistricts);
    }

    // Query recent history to find compiled output files for the current session
    let compiledFiles = [];
    try {
        const res = await fetch("/history");
        const json = await res.json();
        if (json.success && json.data) {
            compiledFiles = json.data.filter(item => {
                if (item.category !== "Mining Files") return false;
                const createdTime = parseDBDate(item.created_at);
                const boundaryTime = jobStartTime ? new Date(jobStartTime.getTime() - 60000) : new Date(Date.now() - 300000);
                return createdTime >= boundaryTime;
            });
        }
    } catch (e) {
        console.error("Failed to query compilation files in modal popup:", e);
    }

    let completedDistricts = [];
    targetDistricts.forEach(dist => {
        const match = compiledFiles.find(f => f.district.toLowerCase() === dist.toLowerCase() && f.file_name.endsWith(".xlsx"));
        if (match) {
            completedDistricts.push({ district: dist, file: match });
        }
    });

    const zipFile = compiledFiles.find(f => f.district === "Multiple Districts" || f.file_name.endsWith(".zip"));

    const fileIcon = document.getElementById("pop-file-icon");
    const fileTypeLabel = document.getElementById("pop-file-type-label");
    const fileNameValue = document.getElementById("pop-file-name-value");
    const popBtnDownloadText = document.getElementById("pop-btn-download-text");
    const btnDownload = document.getElementById("btn-download-output");

    if (targetDistricts.length === 1) {
        fileIcon.textContent = "🟢";
        fileTypeLabel.textContent = "Generated File (Excel Spreadsheet):";
        popBtnDownloadText.textContent = "Download Excel File";

        if (completedDistricts.length === 1) {
            fileNameValue.textContent = completedDistricts[0].file.file_name;
            btnDownload.onclick = () => {
                window.open(`/download/${completedDistricts[0].file.file_id}`, "_blank");
            };
        } else {
            fileNameValue.textContent = "Output file not generated or failed.";
            btnDownload.onclick = () => {
                alert("Output file not found for the selected district.");
            };
        }
    } else {
        fileIcon.textContent = "📦";
        fileTypeLabel.textContent = "Generated File (ZIP Archive):";
        popBtnDownloadText.textContent = "Download ZIP File";

        if (zipFile) {
            fileNameValue.textContent = zipFile.file_name;
            btnDownload.onclick = () => {
                window.open(`/download/${zipFile.file_id}`, "_blank");
            };
        } else if (completedDistricts.length > 0) {
            fileNameValue.textContent = completedDistricts[0].file.file_name;
            btnDownload.onclick = () => {
                window.open(`/download/${completedDistricts[0].file.file_id}`, "_blank");
            };
        } else {
            fileNameValue.textContent = "No successful district files compiled.";
            btnDownload.onclick = () => {
                alert("No output files generated to download.");
            };
        }
    }

    const btnClose = document.getElementById("btn-close-completion");
    btnClose.onclick = () => {
        modal.style.display = "none";
        if (window.loadRecentFiles) {
            window.loadRecentFiles();
        }
    };

    modal.style.display = "flex";
}

function parseDBDate(str) {
    if (!str) return new Date(0);
    const parts = str.split(" ");
    if (parts.length < 2) return new Date(str);
    const dateParts = parts[0].split("-");
    const timeParts = parts[1].split(":");
    return new Date(
        parseInt(dateParts[0]),
        parseInt(dateParts[1]) - 1,
        parseInt(dateParts[2]),
        parseInt(timeParts[0]) || 0,
        parseInt(timeParts[1]) || 0,
        parseInt(timeParts[2]) || 0
    );
}

window.fetchAndShowMiningTerminalLogs = async function () {
    const terminal = document.getElementById("live-terminal");
    if (!terminal) return;
    try {
        const res = await fetch("/logs");
        const data = await res.json();
        if (data.success && data.data) {
            terminal.innerHTML = "";
            const lines = data.data.split("\n");

            // Filter out lines older than consoleClearTime if cleared
            let displayLines = lines;
            if (consoleClearTime) {
                displayLines = lines.filter(line => {
                    if (!line.trim()) return false;
                    const match = line.match(/^\[([^\]]+)\]/);
                    if (match) {
                        const lineDate = new Date(match[1].replace(/-/g, "/"));
                        return lineDate >= consoleClearTime;
                    }
                    return true;
                });
            }

            // Only show last 80 lines in the dashboard live-terminal to keep it clean
            displayLines = displayLines.slice(-80);
            displayLines.forEach(line => {
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
                    div.style.color = "#a855f7"; // Violet/purple for debug
                } else if (line.includes("[INFO]")) {
                    div.style.color = "#00b8d9"; // Light blue for info
                } else {
                    div.style.color = "#919eab"; // Muted text for default system logs
                }

                div.textContent = line;
                terminal.appendChild(div);
            });
            // Auto scroll console if checked
            const autoScrollChk = document.getElementById("chk-auto-scroll");
            if (autoScrollChk && autoScrollChk.checked) {
                terminal.scrollTop = terminal.scrollHeight;
            }
        }
    } catch (err) {
        console.error("Failed to load logs in live terminal: ", err);
    }
};

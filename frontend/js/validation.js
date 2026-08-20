// Lead Quality Validation Dashboard
document.addEventListener("DOMContentLoaded", () => {
    initValidationDashboard();
});

function initValidationDashboard() {
    const dropZone = document.getElementById("drop-zone");
    const fileUploader = document.getElementById("file-uploader");
    const selectedFileLabel = document.getElementById("selected-file-name");
    
    const btnFind = document.getElementById("btn-find-duplicates");
    const btnMark = document.getElementById("btn-mark-duplicates");
    const btnDelete = document.getElementById("btn-delete-duplicates");
    const btnFix = document.getElementById("btn-fix-classification");
    const btnDownload = document.getElementById("btn-download-validated");
    
    // New UI Elements
    const btnValRefresh = document.getElementById("btn-val-refresh");
    const btnValDeleteSelected = document.getElementById("btn-val-delete-selected");
    const valSearchBox = document.getElementById("val-search-box");
    const btnColSelector = document.getElementById("btn-col-selector");
    const colSelectorMenu = document.getElementById("col-selector-menu");
    const colSelectorList = document.getElementById("col-selector-list");
    const chkSelectAllDuplicates = document.getElementById("chk-select-all-duplicates");
    const duplicateGroupsList = document.getElementById("duplicate-groups-list");
    
    const uiTotalGroups = document.getElementById("ui-total-groups");
    const uiTotalRows = document.getElementById("ui-total-rows");
    const uiTotalRowsBadge = document.getElementById("ui-total-rows-badge");
    
    let activeSessionId = null;
    let currentWorkingFileId = null;
    let previewData = [];
    let isDownloadEnabled = false;
    
    // Column Configuration (Ordered exactly like the reference UI)
    let columnsConfig = [
        { id: "name", label: "Organization Name", visible: true },
        { id: "salutation", label: "Salutation", visible: true },
        { id: "first_name", label: "First Name", visible: true },
        { id: "last_name", label: "Last Name", visible: true },
        { id: "title", label: "Title", visible: true },
        { id: "email", label: "Email", visible: true },
        { id: "secondary_email", label: "Secondary Email", visible: true },
        { id: "phone", label: "Phone", visible: true },
        { id: "mobile", label: "Mobile", visible: true },
        { id: "fax", label: "Fax", visible: true },
        { id: "skype_id", label: "Skype ID", visible: true },
        { id: "website", label: "Website", visible: true },
        { id: "instagram", label: "Instagram", visible: true },
        { id: "facebook", label: "Facebook", visible: true },
        { id: "linkedin", label: "LinkedIn", visible: true },
        { id: "twitter", label: "Twitter", visible: true },
        { id: "youtube", label: "YouTube", visible: true },
        { id: "street", label: "Street", visible: true },
        { id: "city", label: "City", visible: true },
        { id: "state", label: "State", visible: true },
        { id: "zip_code", label: "Zip Code", visible: true },
        { id: "country", label: "Country", visible: true },
        { id: "industry", label: "Industry", visible: true },
        { id: "keyword", label: "Keyword", visible: true },
        { id: "tags", label: "Tags", visible: true }
    ];

    // Tracking selection states (Set of row numbers)
    let selectedRowNumbers = new Set();
    let expandedGroups = new Set(); // Group IDs that are expanded
    
    // Statistics Tracking state
    let initialRowCount = 0;
    let markedCount = 0;
    let removedCount = 0;

    // Enable action buttons by default when page opens (except download)
    btnFind.disabled = false;
    btnMark.disabled = false;
    btnDelete.disabled = false;
    btnFix.disabled = false;
    btnDownload.disabled = true;

    // Setup drag-and-drop triggers
    dropZone.addEventListener("click", () => fileUploader.click());
    
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "var(--primary)";
    });
    
    dropZone.addEventListener("dragleave", () => {
        dropZone.style.borderColor = "var(--border-color)";
    });
    
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "var(--border-color)";
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });
    
    fileUploader.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    async function handleFileUpload(file) {
        selectedFileLabel.textContent = `Uploading: ${file.name}...`;
        const formData = new FormData();
        formData.append("file", file);
        
        try {
            const res = await fetch("/validation/upload", {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            
            if (data.success) {
                activeSessionId = data.data.session_id;
                
                // Hide Dropzone and Show Uploaded File Card
                dropZone.style.display = "none";
                
                // Calculate size representation
                const sizeText = file.size > 1024 * 1024 
                    ? (file.size / (1024 * 1024)).toFixed(1) + " MB" 
                    : (file.size / 1024).toFixed(1) + " KB";
                
                // Calculate extension type
                const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
                const typeText = ext === ".csv" ? "CSV" : "Excel";
                
                initialRowCount = data.data.row_count;
                markedCount = 0;
                removedCount = 0;
                
                // Set text fields in Card
                document.getElementById("card-filename").textContent = file.name;
                document.getElementById("card-filesize").textContent = sizeText;
                document.getElementById("card-rows").textContent = initialRowCount;
                document.getElementById("card-filetype").textContent = typeText;
                document.getElementById("card-uploadtime").textContent = new Date().toLocaleTimeString();
                
                document.getElementById("uploaded-file-card").style.display = "flex";
                selectedFileLabel.textContent = "";
                
                // Adjust button states
                isDownloadEnabled = false;
                btnFind.disabled = false;
                btnMark.disabled = false;
                btnDelete.disabled = false;
                btnFix.disabled = false;
                btnDownload.disabled = !isDownloadEnabled;
                
                // Clear previews
                document.getElementById("duplicate-summary-section").style.display = "none";
                document.getElementById("preview-panel").style.display = "none";
            } else {
                selectedFileLabel.textContent = data.detail || "Upload failed.";
                selectedFileLabel.style.color = "var(--danger)";
            }
        } catch (err) {
            console.error("Upload failure: ", err);
            selectedFileLabel.textContent = "Error uploading file.";
            selectedFileLabel.style.color = "var(--danger)";
        }
    }

    // Remove File button handler
    const btnRemoveFile = document.getElementById("btn-remove-file");
    btnRemoveFile.addEventListener("click", () => {
        fileUploader.value = "";
        activeSessionId = null;
        currentWorkingFileId = null;
        previewData = [];
        selectedRowNumbers.clear();
        expandedGroups.clear();
        initialRowCount = 0;
        markedCount = 0;
        removedCount = 0;
        
        // Reset text inputs of cards
        document.getElementById("sum-rows-scanned").textContent = "0";
        document.getElementById("sum-dup-groups").textContent = "0";
        document.getElementById("sum-dup-rows").textContent = "0";
        document.getElementById("sum-phone-dups").textContent = "0";
        document.getElementById("sum-mobile-dups").textContent = "0";
        document.getElementById("sum-address-dups").textContent = "0";
        document.getElementById("sum-email-dups").textContent = "0";
        document.getElementById("sum-website-dups").textContent = "0";
        document.getElementById("sum-name-dups").textContent = "0";
        document.getElementById("sum-rows-marked").textContent = "0";
        document.getElementById("sum-rows-removed").textContent = "0";
        document.getElementById("sum-final-rows").textContent = "0";
        
        // Toggle elements visibility
        document.getElementById("uploaded-file-card").style.display = "none";
        document.getElementById("duplicate-summary-section").style.display = "none";
        document.getElementById("preview-panel").style.display = "none";
        dropZone.style.display = "flex";
        selectedFileLabel.textContent = "";
        
        // Reset action buttons to page load default
        isDownloadEnabled = false;
        btnFind.disabled = false;
        btnMark.disabled = false;
        btnDelete.disabled = false;
        btnFix.disabled = false;
        btnDownload.disabled = !isDownloadEnabled;
    });

    // Trigger Scan / Find Duplicates
    async function runScan() {
        if (!activeSessionId) return;
        selectedFileLabel.textContent = "Scanning duplicate groups...";
        
        try {
            const res = await fetch("/validation/find-duplicates", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: activeSessionId })
            });
            const data = await res.json();
            
            if (data.success) {
                selectedFileLabel.textContent = "Scan complete.";
                
                // Populate metrics summary
                const sum = data.data.summary;
                previewData = data.data.preview;
                
                // Calculate duplicate categories from previewData
                let phoneDups = 0;
                let mobileDups = 0;
                let addressDups = 0;
                let emailDups = 0;
                let websiteDups = 0;
                let nameDups = 0;
                
                previewData.forEach(row => {
                    if (!row.keep) {
                        const reason = row.duplicate_reason || "";
                        if (reason === "Phone Duplicate" || reason === "Phone Matched") {
                            phoneDups++;
                        } else if (reason === "Mobile Duplicate" || reason === "Mobile Matched") {
                            mobileDups++;
                        } else if (reason === "Email Duplicate" || reason === "Email Matched") {
                            emailDups++;
                        } else if (reason === "Website Duplicate" || reason === "Website Matched") {
                            websiteDups++;
                        } else if (reason === "Name + Address Duplicate" || reason === "Business Name + Website + Address") {
                            addressDups++;
                        } else {
                            // Name + Phone, Name + Email, Name + Website, Place ID Duplicate etc.
                            nameDups++;
                        }
                    }
                });
                
                // Update 12-Card Duplicate Summary Section
                document.getElementById("sum-rows-scanned").textContent = sum.rows_scanned;
                document.getElementById("sum-dup-groups").textContent = sum.duplicate_groups;
                document.getElementById("sum-dup-rows").textContent = sum.duplicate_rows;
                document.getElementById("sum-phone-dups").textContent = phoneDups;
                document.getElementById("sum-mobile-dups").textContent = mobileDups;
                document.getElementById("sum-address-dups").textContent = addressDups;
                document.getElementById("sum-email-dups").textContent = emailDups;
                document.getElementById("sum-website-dups").textContent = websiteDups;
                document.getElementById("sum-name-dups").textContent = nameDups;
                document.getElementById("sum-rows-marked").textContent = markedCount;
                document.getElementById("sum-rows-removed").textContent = removedCount;
                document.getElementById("sum-final-rows").textContent = sum.rows_scanned;
                
                document.getElementById("duplicate-summary-section").style.display = "block";
                
                // Update new UI headers & metrics
                uiTotalRowsBadge.textContent = `${sum.duplicate_rows} Duplicate Rows Found`;
                uiTotalGroups.textContent = sum.duplicate_groups;
                uiTotalRows.textContent = sum.duplicate_rows;
                
                // Reset selection: Original unchecked, Duplicates checked by default
                selectedRowNumbers.clear();
                previewData.forEach(row => {
                    if (!row.keep) {
                        selectedRowNumbers.add(row.row_number);
                    }
                });
                
                // Expand all group cards initially
                expandedGroups.clear();
                const grouped = getGroupedData(previewData);
                Object.keys(grouped).forEach(gId => expandedGroups.add(Number(gId)));
                
                renderDuplicatePreview();
                document.getElementById("preview-panel").style.display = "block";
                
                // Action Buttons state rule
                btnFind.disabled = false;
                btnMark.disabled = false;
                btnDelete.disabled = false;
                btnFix.disabled = false;
                btnDownload.disabled = !isDownloadEnabled;
                btnValDeleteSelected.disabled = selectedRowNumbers.size === 0;
            }
        } catch (err) {
            console.error("Find duplicates failure: ", err);
        }
    }

    btnFind.addEventListener("click", runScan);
    btnValRefresh.addEventListener("click", runScan);

    // Grouping helper
    function getGroupedData(rows) {
        const groups = {};
        rows.forEach(row => {
            const gid = row.group_id;
            if (!groups[gid]) {
                groups[gid] = [];
            }
            groups[gid].push(row);
        });
        
        const duplicateGroups = {};
        Object.entries(groups).forEach(([gid, groupRows]) => {
            if (groupRows.length > 1) {
                duplicateGroups[gid] = groupRows;
            }
        });
        return duplicateGroups;
    }

    // Main Renderer for the Cards-based UI
    function renderDuplicatePreview() {
        const grouped = getGroupedData(previewData);
        
        // Handle Search Filtering
        const query = valSearchBox.value.trim().toLowerCase();
        let filteredGroups = {};
        
        if (query) {
            Object.entries(grouped).forEach(([gid, groupRows]) => {
                const matches = groupRows.some(row => {
                    return (
                        String(row.name || "").toLowerCase().includes(query) ||
                        String(row.phone || "").toLowerCase().includes(query) ||
                        String(row.mobile || "").toLowerCase().includes(query) ||
                        String(row.email || "").toLowerCase().includes(query) ||
                        String(row.website || "").toLowerCase().includes(query) ||
                        String(row.street || "").toLowerCase().includes(query) ||
                        String(row.city || "").toLowerCase().includes(query) ||
                        String(row.state || "").toLowerCase().includes(query) ||
                        String(row.industry || "").toLowerCase().includes(query) ||
                        String(row.keyword || "").toLowerCase().includes(query) ||
                        String(row.tags || "").toLowerCase().includes(query)
                    );
                });
                if (matches) {
                    filteredGroups[gid] = groupRows;
                }
            });
        } else {
            filteredGroups = grouped;
        }

        // Render Group Cards
        duplicateGroupsList.innerHTML = "";
        
        const groupEntries = Object.entries(filteredGroups);
        
        if (groupEntries.length === 0) {
            duplicateGroupsList.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-muted); background: var(--bg-element); border: 1px solid var(--border-color); border-radius: 8px;">
                    No duplicate groups found matching search query.
                </div>
            `;
            btnValDeleteSelected.disabled = true;
            return;
        }

        let allDupRowsCount = 0;
        let selectedDupRowsCount = 0;

        groupEntries.forEach(([gid, groupRows]) => {
            const groupId = Number(gid);
            const groupSize = groupRows.length;
            
            // Extract row numbers for Rows info (e.g. Rows: 20, 46)
            const allGroupRowNums = groupRows.map(r => r.row_number).sort((a,b)=>a-b);
            const rowsText = allGroupRowNums.join(", ");
            
            // Extract duplicate row numbers to display under "Matches Row" in the original badge
            const dupRowsInGroup = groupRows.filter(r => !r.keep);
            const dupRowNums = dupRowsInGroup.map(r => r.row_number).sort((a,b)=>a-b);
            const matchesText = dupRowNums.join(", ");

            allDupRowsCount += dupRowsInGroup.length;
            const selectedInGroup = dupRowsInGroup.filter(r => selectedRowNumbers.has(r.row_number));
            selectedDupRowsCount += selectedInGroup.length;
            
            const groupChecked = dupRowsInGroup.length > 0 && selectedInGroup.length === dupRowsInGroup.length;

            // Generate card element
            const card = document.createElement("div");
            card.className = "duplicate-group-card";
            
            const isExpanded = expandedGroups.has(groupId);

            card.innerHTML = `
                <div class="group-card-header">
                    <div class="header-left-info">
                        <input type="checkbox" class="group-checkbox" data-group-id="${groupId}" ${groupChecked ? 'checked' : ''} />
                        <span class="group-icon-folder">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00b8d9" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                            </svg>
                        </span>
                        <span class="group-title-label">Duplicate Group #${groupId}</span>
                        <span class="badge-records">${groupSize} Records</span>
                    </div>
                    <div class="header-right-info">
                        <span class="rows-label-text">Rows: ${rowsText}</span>
                        <button class="btn-toggle-group">
                            ${isExpanded ? '▲' : '▼'}
                        </button>
                    </div>
                </div>
                
                <div class="group-card-body" style="display: ${isExpanded ? 'block' : 'none'};">
                    <div class="table-scroll">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th style="width: 50px; text-align: center;">Select</th>
                                    <th style="width: 50px; text-align: center;">#</th>
                                    <th style="width: 70px; text-align: center;">Group ID</th>
                                    <th style="width: 250px;">Status / Reason</th>
                                    ${columnsConfig.filter(c => c.visible).map(c => `<th>${c.label}</th>`).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                <!-- Rows loaded dynamically -->
                            </tbody>
                        </table>
                    </div>
                </div>
            `;

            const tbody = card.querySelector("tbody");
            
            groupRows.forEach((row, rIdx) => {
                const tr = document.createElement("tr");
                
                // Color rows: original is dark blue, duplicate is dark grey
                if (row.keep) {
                    tr.className = "row-role-original";
                } else {
                    tr.className = "row-role-duplicate";
                }

                // Checkbox Column
                const isRowChecked = selectedRowNumbers.has(row.row_number);
                const chkHtml = `
                    <td style="text-align: center; padding: 12px 16px;">
                        <input type="checkbox" class="row-checkbox" data-row-number="${row.row_number}" data-group-id="${groupId}" ${isRowChecked ? 'checked' : ''} />
                    </td>
                `;

                // Sequence Index Column
                const seqHtml = `<td style="text-align: center; font-weight: 600; padding: 12px 16px;">${rIdx + 1}</td>`;

                // Group ID Column
                const gidHtml = `<td style="text-align: center; color: var(--text-secondary); padding: 12px 16px;">${row.group_id}</td>`;

                // Status Badge Column with Check Circle (Original) or Danger Badge (Duplicate)
                let badgeHtml = "";
                if (row.keep) {
                    badgeHtml = `
                        <td style="padding: 12px 16px;">
                            <div class="status-badge-container">
                                <span class="badge-dot dot-green"></span>
                                <div class="status-text-block">
                                    <span class="status-title-text green-text">Original Record</span>
                                    <span class="status-desc-text">Original record kept. Matches Row ${matchesText}</span>
                                </div>
                            </div>
                        </td>
                    `;
                } else {
                    badgeHtml = `
                        <td style="padding: 12px 16px;">
                            <div class="status-badge-container">
                                <span class="badge-dot dot-red"></span>
                                <div class="status-text-block">
                                    <span class="status-title-text red-text">Duplicate Record</span>
                                    <span class="status-desc-text">Duplicate of Row ${groupId}</span>
                                </div>
                            </div>
                        </td>
                    `;
                }

                // Render dynamic configuration columns
                let colsHtml = "";
                columnsConfig.filter(c => c.visible).forEach(col => {
                    let val = row[col.id] || "N/A";
                    
                    if (col.id === "website" && val !== "N/A") {
                        colsHtml += `<td style="padding: 12px 16px; white-space: nowrap;"><a href="${val}" target="_blank" style="color:var(--primary); text-decoration:none;">${val}</a></td>`;
                    } else {
                        colsHtml += `<td style="padding: 12px 16px; white-space: nowrap; max-width: 220px; overflow: hidden; text-overflow: ellipsis;">${val}</td>`;
                    }
                });

                tr.innerHTML = chkHtml + seqHtml + gidHtml + badgeHtml + colsHtml;
                tbody.appendChild(tr);
            });

            // Bind card expand/collapse toggle
            const header = card.querySelector(".group-card-header");
            const body = card.querySelector(".group-card-body");
            const toggleBtn = card.querySelector(".btn-toggle-group");

            header.addEventListener("click", (e) => {
                // Ignore if check click
                if (e.target.tagName.toLowerCase() === "input") return;
                
                if (expandedGroups.has(groupId)) {
                    expandedGroups.delete(groupId);
                    body.style.display = "none";
                    toggleBtn.textContent = "▼";
                } else {
                    expandedGroups.add(groupId);
                    body.style.display = "block";
                    toggleBtn.textContent = "▲";
                }
            });

            // Bind Group Checkbox Change
            const grpChk = card.querySelector(".group-checkbox");
            grpChk.addEventListener("change", (e) => {
                const checked = e.target.checked;
                dupRowsInGroup.forEach(r => {
                    if (checked) {
                        selectedRowNumbers.add(r.row_number);
                    } else {
                        selectedRowNumbers.delete(r.row_number);
                    }
                });
                syncSelectAllButton();
                renderDuplicatePreview();
            });

            // Bind Row Checkbox Change (Allows selecting/deselecting both original and duplicate rows)
            card.querySelectorAll(".row-checkbox").forEach(chk => {
                chk.addEventListener("change", (e) => {
                    const rowNum = Number(e.target.dataset.rowNumber);
                    if (e.target.checked) {
                        selectedRowNumbers.add(rowNum);
                    } else {
                        selectedRowNumbers.delete(rowNum);
                    }
                    syncSelectAllButton();
                    renderDuplicatePreview();
                });
            });

            duplicateGroupsList.appendChild(card);
        });

        // Sync main Select All Checkbox (Only represents duplicate rows checked)
        chkSelectAllDuplicates.checked = allDupRowsCount > 0 && selectedDupRowsCount === allDupRowsCount;
        btnValDeleteSelected.disabled = selectedRowNumbers.size === 0;
    }

    function syncSelectAllButton() {
        const grouped = getGroupedData(previewData);
        let allDupRowsCount = 0;
        Object.values(grouped).forEach(groupRows => {
            groupRows.forEach(row => {
                if (!row.keep) allDupRowsCount++;
            });
        });
        
        // Check if all duplicates are currently checked
        let selectedDupsCount = 0;
        previewData.forEach(row => {
            if (!row.keep && selectedRowNumbers.has(row.row_number)) {
                selectedDupsCount++;
            }
        });
        
        chkSelectAllDuplicates.checked = allDupRowsCount > 0 && selectedDupsCount === allDupRowsCount;
        btnValDeleteSelected.disabled = selectedRowNumbers.size === 0;
    }

    // Select All Duplicates checkbox handler (Checking it selects all duplicates, leaving original rows unchecked)
    chkSelectAllDuplicates.addEventListener("change", (e) => {
        const checked = e.target.checked;
        previewData.forEach(row => {
            if (!row.keep) {
                if (checked) {
                    selectedRowNumbers.add(row.row_number);
                } else {
                    selectedRowNumbers.delete(row.row_number);
                }
            }
        });
        renderDuplicatePreview();
    });

    // Column selector dropdown toggle
    btnColSelector.addEventListener("click", (e) => {
        e.stopPropagation();
        colSelectorMenu.style.display = colSelectorMenu.style.display === "none" ? "block" : "none";
    });

    document.addEventListener("click", (e) => {
        if (!colSelectorMenu.contains(e.target) && e.target !== btnColSelector) {
            colSelectorMenu.style.display = "none";
        }
    });

    // Render Columns Show/Hide list
    function renderColumnSelector() {
        colSelectorList.innerHTML = "";
        columnsConfig.forEach((col, idx) => {
            const div = document.createElement("div");
            div.style.display = "flex";
            div.style.alignItems = "center";
            div.style.justifyContent = "space-between";
            div.style.padding = "4px 8px";
            div.style.background = "var(--bg-element)";
            div.style.borderRadius = "4px";
            div.style.border = "1px solid var(--border-color)";
            
            div.innerHTML = `
                <label style="display:flex; align-items:center; gap:6px; font-size:12px; cursor:pointer; color:var(--text-primary); margin:0; user-select:none;">
                    <input type="checkbox" class="col-visibility-chk" data-id="${col.id}" ${col.visible ? 'checked' : ''} style="cursor:pointer;" />
                    <span>${col.label}</span>
                </label>
                <div style="display:flex; gap:4px;">
                    <button class="btn-col-up" data-idx="${idx}" style="background:none; border:none; color:var(--text-secondary); cursor:pointer; font-size:10px; padding:2px 4px;">▲</button>
                    <button class="btn-col-down" data-idx="${idx}" style="background:none; border:none; color:var(--text-secondary); cursor:pointer; font-size:10px; padding:2px 4px;">▼</button>
                </div>
            `;

            // Checkbox toggle
            div.querySelector(".col-visibility-chk").addEventListener("change", (e) => {
                col.visible = e.target.checked;
                renderDuplicatePreview();
            });

            // Reorder Move Up
            div.querySelector(".btn-col-up").addEventListener("click", (e) => {
                e.stopPropagation();
                const curIdx = Number(e.currentTarget.dataset.idx);
                if (curIdx > 0) {
                    const temp = columnsConfig[curIdx];
                    columnsConfig[curIdx] = columnsConfig[curIdx - 1];
                    columnsConfig[curIdx - 1] = temp;
                    renderColumnSelector();
                    renderDuplicatePreview();
                }
            });

            // Reorder Move Down
            div.querySelector(".btn-col-down").addEventListener("click", (e) => {
                e.stopPropagation();
                const curIdx = Number(e.currentTarget.dataset.idx);
                if (curIdx < columnsConfig.length - 1) {
                    const temp = columnsConfig[curIdx];
                    columnsConfig[curIdx] = columnsConfig[curIdx + 1];
                    columnsConfig[curIdx + 1] = temp;
                    renderColumnSelector();
                    renderDuplicatePreview();
                }
            });

            colSelectorList.appendChild(div);
        });
    }

    renderColumnSelector();

    // Bind search box input (live filtering)
    valSearchBox.addEventListener("input", () => {
        renderDuplicatePreview();
    });

    // Delete Selected duplicates handler
    async function deleteSelectedDuplicates() {
        if (!activeSessionId) return;
        
        // Extract only duplicate row numbers that are currently selected (enforcing original rows are never deleted)
        const dupRowsToDelete = Array.from(selectedRowNumbers).filter(rowNum => {
            const row = previewData.find(r => r.row_number === rowNum);
            return row && !row.keep;
        });

        if (dupRowsToDelete.length === 0) {
            alert("No duplicate rows are selected for deletion.");
            return;
        }

        if (!confirm(`Are you sure you want to delete the ${dupRowsToDelete.length} selected duplicate rows?`)) {
            return;
        }

        selectedFileLabel.textContent = "Deleting selected duplicates...";
        btnValDeleteSelected.disabled = true;
        btnDelete.disabled = true;

        try {
            const res = await fetch("/validation/delete", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: activeSessionId,
                    delete_row_numbers: dupRowsToDelete
                })
            });
            const data = await res.json();
            
            if (data.success) {
                currentWorkingFileId = data.data.file_id;
                alert("Selected duplicate rows deleted successfully!");
                
                removedCount += dupRowsToDelete.length;
                selectedRowNumbers.clear();
                await runScan(); // refresh groups lists and counters
                
                isDownloadEnabled = true;
                btnFind.disabled = false;
                btnMark.disabled = false;
                btnDelete.disabled = false;
                btnFix.disabled = false;
                btnDownload.disabled = !isDownloadEnabled;
            } else {
                alert(data.detail || "Deletion failed.");
                btnValDeleteSelected.disabled = false;
                btnDelete.disabled = false;
            }
        } catch (err) {
            console.error("Delete duplicates failure: ", err);
            selectedFileLabel.textContent = "Deletion error.";
            selectedFileLabel.style.color = "var(--danger)";
            btnValDeleteSelected.disabled = false;
            btnDelete.disabled = false;
        }
    }

    btnValDeleteSelected.addEventListener("click", deleteSelectedDuplicates);
    btnDelete.addEventListener("click", deleteSelectedDuplicates);

    // Mark Duplicates
    btnMark.addEventListener("click", async () => {
        if (!activeSessionId) return;
        try {
            const res = await fetch("/validation/mark", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: activeSessionId })
            });
            const data = await res.json();
            if (data.success) {
                currentWorkingFileId = data.data.file_id;
                markedCount = previewData.filter(r => !r.keep).length;
                document.getElementById("sum-rows-marked").textContent = markedCount;
                alert("Marked spreadsheet generated. Go to Recent Files or click Download.");
                isDownloadEnabled = true;
                btnFind.disabled = false;
                btnMark.disabled = false;
                btnDelete.disabled = false;
                btnFix.disabled = false;
                btnDownload.disabled = !isDownloadEnabled;
            }
        } catch (err) {
            console.error("Mark duplicates failure: ", err);
        }
    });

    // Fix Industry & Tag
    btnFix.addEventListener("click", async () => {
        if (!activeSessionId) return;
        selectedFileLabel.textContent = "Correcting Industries and Tags in-place...";
        btnFix.disabled = true;
        
        try {
            const res = await fetch("/validation/fix-classification", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: activeSessionId })
            });
            const data = await res.json();
            if (data.success) {
                currentWorkingFileId = data.data.file_id;
                selectedFileLabel.textContent = "Industry classifications corrected!";
                selectedFileLabel.style.color = "var(--success)";
                btnFind.disabled = false;
                btnMark.disabled = false;
                btnDelete.disabled = false;
                btnFix.disabled = false;
                btnDownload.disabled = !isDownloadEnabled;
            }
        } catch (err) {
            console.error("Fix classification failure: ", err);
            btnFix.disabled = false;
        }
    });

    // Download Working File
    btnDownload.addEventListener("click", () => {
        if (!currentWorkingFileId) return;
        window.open(`/download/${currentWorkingFileId}`, "_blank");
    });
}

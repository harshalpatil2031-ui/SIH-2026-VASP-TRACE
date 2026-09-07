/**
 * Main Application Logic for VASP TRACE: 3-Screen Cybercrime Intelligence Platform
 * Screen 1: Simple Login / Landing Screen
 * Screen 2: Investigation Dashboard (Create Case & Previous Cases)
 * Screen 3: Investigation Analysis Page (Graph, Attribution, Cross-Case, SAHYOG, Report)
 */

let state = {
    currentCaseId: "CASE-147",
    traceData: null,
    isTraced: false
};

// Initialize App on Load
document.addEventListener("DOMContentLoaded", () => {
    // Bind node tap listener from graph.js
    window.onNodeSelected = (node) => {
        showNodeInspector(node);
    };
    window.onNodeDeselected = () => {
        hideNodeInspector();
    };

    // Start on Screen 1 (Login Screen)
    goToScreen("LOGIN");
});

// Helper to fill last used profile on Screen 1
function fillLastUsedProfile() {
    const emailInput = document.getElementById("loginOfficerEmail");
    const badgeInput = document.getElementById("loginOfficerBadge");
    if (emailInput) emailInput.value = "harshal.patil2031@gmail.com";
    if (badgeInput) badgeInput.value = "SP • Cyber Crime Unit";
}

// Authenticate and open Screen 2
function authenticateOfficerAndEnter() {
    const emailInput = document.getElementById("loginOfficerEmail");
    const badgeInput = document.getElementById("loginOfficerBadge");
    
    const email = emailInput && emailInput.value.trim() ? emailInput.value.trim() : "harshalpatil.2031@gmail.com";
    const badge = badgeInput && badgeInput.value.trim() ? badgeInput.value.trim() : "SP • Cyber Crime Unit";

    // Update Header Officer Names
    const headerOfficer = document.getElementById("headerOfficerName");
    if (headerOfficer) headerOfficer.innerText = badge.includes("•") ? badge.split("•")[0].trim() : badge;

    goToScreen("DASHBOARD");
}

// ================= 3-SCREEN MULTI-VIEW NAVIGATION =================

function goToScreen(screen) {
    const sLogin = document.getElementById("screenLogin");
    const sDash = document.getElementById("screenDashboard");
    const sAnalysis = document.getElementById("screenAnalysis");

    sLogin.classList.add("hidden");
    sDash.classList.add("hidden");
    sAnalysis.classList.add("hidden");

    if (screen === "LOGIN") {
        sLogin.classList.remove("hidden");
    } else if (screen === "DASHBOARD") {
        sDash.classList.remove("hidden");
    } else if (screen === "ANALYSIS") {
        sAnalysis.classList.remove("hidden");
        // Ensure Cytoscape container is initialized after DOM is visible
        setTimeout(() => {
            if (!cy) {
                initCytoscape("cy");
            } else {
                cy.resize();
            }
        }, 100);
    }
}

// Launch Analysis from Screen 2 (Create New Case Form)
async function launchAnalysisFromDashboard() {
    const fir = document.getElementById("dashFIR").value.trim();
    const wallet = document.getElementById("dashWallet").value.trim();
    const chain = document.getElementById("dashChain").value;
    const amount = parseInt(document.getElementById("dashAmount").value) || 180000;
    const notes = document.getElementById("dashNotes").value.trim();

    try {
        const createRes = await fetch("/api/cases/create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                fir_number: fir || "FIR/2026/CY-ADHOC/991",
                suspect_wallet: wallet || "0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97",
                chain: chain || "TRON",
                amount_inr: amount,
                notes: notes || "Suspect wallet fund tracing"
            })
        });
        if (!createRes.ok) {
            const errObj = await createRes.json().catch(() => ({}));
            alert("⚠️ Invalid Wallet Address: " + (errObj.detail || "Please enter a valid crypto wallet address format."));
            return;
        }
        const createData = await createRes.json();
        if (createData && createData.case_id) {
            state.currentCaseId = createData.case_id;
        } else {
            state.currentCaseId = (wallet.startsWith("TJ9k") ? "CASE-147" : (wallet.startsWith("0x48") ? "CASE-101" : "CUSTOM"));
        }
    } catch (e) {
        console.warn("Case creation error:", e);
        if (e.message && e.message.includes("Invalid")) {
            alert("⚠️ " + e.message);
            return;
        }
        state.currentCaseId = (wallet.startsWith("TJ9k") ? "CASE-147" : (wallet.startsWith("0x48") ? "CASE-101" : "CUSTOM"));
    }

    // Populate Screen 3 Workbench
    document.getElementById("caseHeaderFIR").innerText = fir || "FIR/2026/CY-ADHOC/991";
    document.getElementById("inputWallet").value = wallet;
    document.getElementById("selectChain").value = chain;
    document.getElementById("caseHeaderAmount").innerText = `₹${amount.toLocaleString()}`;
    document.getElementById("caseNotes").innerText = notes;

    // Switch to Screen 3 and run trace
    goToScreen("ANALYSIS");
    setTimeout(() => {
        triggerTrace();
    }, 150);
}

// Open Specific Case from Screen 2 Previous Cases Table
async function openCaseInWorkbench(caseId) {
    state.currentCaseId = caseId;
    goToScreen("ANALYSIS");

    // Populate case details into inputs without running immediately
    await selectCase(caseId, false);
}

// Switch Case in Screen 3 (Quick Pills)
async function selectCase(caseId, autoRun = false) {
    state.currentCaseId = caseId;
    state.isTraced = false;
    
    // Ensure trace button is enabled
    const btnTrace = document.getElementById("btnTrace");
    if (btnTrace) btnTrace.disabled = false;

    // Update top pill active states
    document.querySelectorAll(".case-pill").forEach(btn => {
        btn.classList.remove("bg-cyan-500/20", "border-cyan-500", "text-cyan-300", "font-bold");
        btn.classList.add("bg-slate-800/80", "border-slate-700", "text-slate-400");
    });
    
    const activeBtn = document.getElementById(`pill-${caseId.toLowerCase()}`);
    if (activeBtn) {
        activeBtn.classList.remove("bg-slate-800/80", "border-slate-700", "text-slate-400");
        activeBtn.classList.add("bg-cyan-500/20", "border-cyan-500", "text-cyan-300", "font-bold");
    }

    // Reset graph to initial placeholder state
    resetToUntracedState();

    try {
        if (caseId === "CUSTOM") {
            document.getElementById("inputWallet").value = "0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97";
            document.getElementById("selectChain").value = "Ethereum";
            document.getElementById("caseHeaderTitle").innerText = "Custom Wallet Investigation";
            document.getElementById("caseHeaderFIR").innerText = "FIR/2026/CY-ADHOC/991";
            document.getElementById("caseHeaderStation").innerText = "Cyber Crime Investigation Unit";
            document.getElementById("caseHeaderAmount").innerText = "₹2,50,000";
            document.getElementById("caseNotes").innerText = "Enter any suspect wallet address to trace which exchange it deposited stolen funds into.";
            if (autoRun) triggerTrace();
            return;
        }

        const res = await fetch(`/api/cases/${caseId}`);
        const caseMeta = await res.json();
        
        // Populate Inputs & Case Header
        document.getElementById("inputWallet").value = caseMeta.suspect_wallet;
        document.getElementById("selectChain").value = caseMeta.chain.includes("TRON") ? "TRON" : "Ethereum";
        document.getElementById("caseHeaderTitle").innerText = caseMeta.title;
        document.getElementById("caseHeaderFIR").innerText = caseMeta.fir_number;
        document.getElementById("caseHeaderStation").innerText = caseMeta.police_station;
        document.getElementById("caseHeaderAmount").innerText = `₹${caseMeta.amount_inr.toLocaleString()}`;
        document.getElementById("caseNotes").innerText = caseMeta.notes;

        if (autoRun) {
            await triggerTrace();
        }

    } catch (err) {
        console.error("Failed to load case", err);
    }
}

// Reset UI to Waiting/Placeholder State before tracing
function resetToUntracedState() {
    clearGraphCanvas();
    const placeholder = document.getElementById("graphPlaceholder");
    if (placeholder) placeholder.classList.remove("hidden");
    
    const terminal = document.getElementById("graphLoadingTerminal");
    if (terminal) terminal.classList.add("hidden");

    const alertBox = document.getElementById("crossCaseAlertBox");
    if (alertBox) alertBox.classList.add("hidden");

    document.getElementById("vaspConfidenceValue").innerText = "--%";
    document.getElementById("vaspNamePrimary").innerText = "Awaiting Trace";
    document.getElementById("vaspChainDisplay").innerText = "Click analyze wallet to start";
    document.getElementById("explainabilityList").innerHTML = `
        <div class="p-3 text-center text-slate-500 text-xs italic bg-slate-900/50 rounded-lg border border-slate-800 font-mono">
            Click 'ANALYZE WALLET' on the left to activate VASP attribution.
        </div>
    `;
    document.getElementById("evidenceHashDisplay").innerText = "Awaiting analysis...";
    const runDisplay = document.getElementById("traceRunIdDisplay");
    if (runDisplay) runDisplay.innerText = "Awaiting trace...";
}

// ================= SCREEN 3: TRIGGER MULTI-HOP TRACE PIPELINE =================

async function triggerTrace() {
    // Ensure Cytoscape is initialized and resized to active container
    if (!cy) {
        initCytoscape("cy");
    } else {
        cy.resize();
    }

    const walletInput = document.getElementById("inputWallet");
    const wallet = walletInput ? walletInput.value.trim() : "TJ9kLpBw81xPqrN4x78G44mX2e1Vb889Zq";
    const chainSelect = document.getElementById("selectChain");
    const chain = chainSelect ? chainSelect.value : "TRON";
    const traceModeSelect = document.getElementById("selectTraceMode");
    const traceMode = traceModeSelect ? traceModeSelect.value : "DEMO";
    const slider = document.getElementById("sliderHops");
    const maxHops = slider ? parseInt(slider.value) : 4;

    // Hide placeholder overlay and show live loading terminal
    const placeholder = document.getElementById("graphPlaceholder");
    if (placeholder) placeholder.classList.add("hidden");
    
    const terminal = document.getElementById("graphLoadingTerminal");
    if (terminal) terminal.classList.remove("hidden");

    // Reset terminal steps
    const s1 = document.getElementById("progStep1");
    const s2 = document.getElementById("progStep2");
    const s3 = document.getElementById("progStep3");
    const s4 = document.getElementById("progStep4");

    if (s1) { s1.className = "text-cyan-400 font-bold"; s1.innerText = "⚡ Fetching on-chain blockchain transaction blocks..."; }
    if (s2) { s2.className = "text-slate-500"; s2.innerText = "⏳ Tracing fund movements..."; }
    if (s3) { s3.className = "text-slate-500"; s3.innerText = "⏳ Building wallet graph..."; }
    if (s4) { s4.className = "text-slate-500"; s4.innerText = "⏳ Identifying entities & VASP..."; }

    const btn = document.getElementById("btnTrace");
    if (btn) btn.disabled = true;

    // Fast simulated sequence progression
    setTimeout(() => {
        if (s1) { s1.className = "text-emerald-400 font-bold"; s1.innerText = "✅ Blockchain data retrieved"; }
        if (s2) { s2.className = "text-cyan-400 font-bold"; s2.innerText = "⚡ Tracing multi-hop peeling chains..."; }
    }, 200);

    setTimeout(() => {
        if (s2) { s2.className = "text-emerald-400 font-bold"; s2.innerText = "✅ Multi-hop transactions traced"; }
        if (s3) { s3.className = "text-cyan-400 font-bold"; s3.innerText = "⚡ Building NetworkX directed graph..."; }
    }, 450);

    setTimeout(() => {
        if (s3) { s3.className = "text-emerald-400 font-bold"; s3.innerText = "✅ Directed graph constructed"; }
        if (s4) { s4.className = "text-cyan-400 font-bold"; s4.innerText = "⚡ Matching VASP deposit sweep heuristics..."; }
    }, 700);

    let requestDeadline;
    try {
        const payload = {
            case_id: state.currentCaseId || "CASE-147",
            wallet_address: wallet,
            chain: chain,
            max_hops: maxHops,
            trace_mode: traceMode
        };
        let data;
        if ((traceMode === "LIVE" || traceMode === "AUTO") && wallet) {
            const start = await fetch("/api/trace/jobs", {
                method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
            });
            const job = await start.json();
            if (!start.ok) throw new Error(job.detail || "Could not start live trace.");
            if (s4) s4.innerText = `⚡ Live evidence scan running (${job.job_id})...`;
            data = await waitForLiveTrace(job.job_id, s4);
        } else {
            const controller = new AbortController();
            requestDeadline = setTimeout(() => controller.abort(), 28000);
            const response = await fetch("/api/trace", {
                method: "POST", headers: { "Content-Type": "application/json" },
                signal: controller.signal, body: JSON.stringify(payload)
            });
            clearTimeout(requestDeadline);
            if (!response.ok) {
                const errObj = await response.json().catch(() => ({}));
                throw new Error(errObj.detail || `HTTP Error: ${response.status}`);
            }
            data = await response.json();
        }
        state.traceData = data;
        state.isTraced = true;

        // Display a completed job immediately.  A prior nested animation left
        // some completed LIVE results behind the loading/placeholder state.
        if (s4) { s4.className = "text-emerald-400 font-bold"; s4.innerText = "✅ VASP Attribution & Cross-Case Complete"; }
        if (terminal) terminal.classList.add("hidden");

        // Ensure Cytoscape is initialized and resized
        if (!cy) initCytoscape("cy");
        cy.resize();

        const headerBadge = document.getElementById("step2HeaderBadge");
        if (headerBadge) headerBadge.className = "flex items-center justify-between bg-cyan-950/40 border border-cyan-500/40 px-3.5 py-2 rounded-xl text-cyan-300 text-xs font-bold font-mono";
                
        const dot = document.getElementById("step2Dot");
        if (dot) dot.className = "w-2 h-2 rounded-full bg-cyan-400";

        const status = document.getElementById("step2Status");
        if (status) {
            const events = data.trace_provenance?.source_events || [];
            const providerFailed = events.some(event => event.status === "FAILED");
            status.innerText = providerFailed
                ? `${data.trace_provenance?.data_mode || traceMode} • Provider retrieval issue — ${data.graph.edges.length} confirmed transfers`
                : `${data.trace_provenance?.data_mode || traceMode} • ${data.graph.edges.length} Transfers Traced`;
        }

                // A large live graph must not prevent the completed evidence
                // result and attribution status from being displayed.
        try {
            renderGraphData(data.graph.nodes || [], data.graph.edges || []);
        } catch (graphError) {
            console.error("Graph rendering error:", graphError);
            if (status) status.innerText = `${data.trace_provenance?.data_mode || traceMode} • ${data.graph.edges.length} transfers retrieved; graph rendering needs review`;
        }

                // Update Explainable VASP Attribution Card
        renderAttribution(data.attribution, data.case_metadata.chain);
        renderActionEligibility(data.action_eligibility, data.suggested_lawful_action);

                // Update Cross-Case Intelligence Alert Banner
        renderCrossCaseAlert(data.cross_case_alert);

                // Update Evidence Hash Stamp
        renderEvidenceSeal(data.evidence_seal);
        renderTraceManifest(data.trace_manifest);

        if (btn) btn.disabled = false;

    } catch (err) {
        console.error("Error executing trace:", err);
        if (terminal) terminal.classList.add("hidden");
        if (btn) btn.disabled = false;
        const message = err.name === "AbortError"
            ? "The live providers did not respond within 28 seconds. Check the provider/network connection, then try again."
            : err.message;
        alert("Trace Error: " + message);
    } finally {
        if (requestDeadline) clearTimeout(requestDeadline);
    }
}

async function waitForLiveTrace(jobId, step) {
    for (;;) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        const response = await fetch(`/api/trace/jobs/${encodeURIComponent(jobId)}`);
        const job = await response.json();
        if (!response.ok) throw new Error(job.detail || "Unable to read live trace status.");
        if (job.status === "COMPLETED") return job.result;
        if (job.status === "FAILED") throw new Error(job.error || "Live trace failed.");
        if (step) step.innerText = `⚡ Live provider scan ${job.status.toLowerCase()} — evidence job ${jobId}`;
    }
}

function renderTraceManifest(manifest) {
    const runDisplay = document.getElementById("traceRunIdDisplay");
    if (runDisplay) runDisplay.innerText = manifest?.investigation_run_id || "Not saved";
}

async function verifySavedEvidenceRun() {
    const runId = state.traceData?.trace_manifest?.investigation_run_id;
    if (!runId) {
        alert("Run a trace first to create an evidence record.");
        return;
    }
    try {
        const response = await fetch(`/api/evidence/runs/${encodeURIComponent(runId)}/verify`, { method: "POST" });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || "Verification failed");
        alert(result.is_valid
            ? `Evidence run verified. ${result.transaction_count} recorded transfers are unchanged.`
            : "Evidence run verification failed. Do not rely on this export until it is reviewed.");
    } catch (error) {
        alert("Run verification error: " + error.message);
    }
}

async function exportEvidencePackage() {
    const runId = state.traceData?.trace_manifest?.investigation_run_id;
    if (!runId) {
        alert("Run a trace first to create an evidence package.");
        return;
    }
    try {
        const response = await fetch(`/api/evidence/runs/${encodeURIComponent(runId)}/export`);
        const packageData = await response.json();
        if (!response.ok) throw new Error(packageData.detail || "Export failed");
        const blob = new Blob([JSON.stringify(packageData, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${runId}_evidence_package.json`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    } catch (error) {
        alert("Evidence export error: " + error.message);
    }
}

// Render Explainable Attribution Section
function renderAttribution(attr, chainName) {
    if (!attr) return;
    const observedLead = (attr.observed_unqualified_candidates || [])[0];
    const vaspConf = document.getElementById("vaspConfidenceValue");
    if (vaspConf) vaspConf.innerText = `${attr.confidence_score}%`;

    const vaspName = document.getElementById("vaspNamePrimary");
    if (vaspName) vaspName.innerText = attr.primary_vasp ? attr.primary_vasp.vasp_name : "Unknown VASP";

    const vaspChain = document.getElementById("vaspChainDisplay");
    if (vaspChain) {
        vaspChain.innerText = attr.confidence_score > 0
            ? `Blockchain: ${chainName} • Distance: ${attr.total_hops} Transfers away`
            : `Blockchain: ${chainName} • Examined scope: ${attr.total_hops} confirmed transfers`;
    }

    // Do not silently hide a labelled exchange that fell below the evidence
    // threshold.  It is an investigative lead, not an attribution.
    const existingLead = document.getElementById("observedVaspLead");
    if (existingLead) existingLead.remove();
    if (observedLead && vaspChain) {
        const lead = document.createElement("div");
        lead.id = "observedVaspLead";
        lead.className = "mt-3 p-2.5 rounded-lg border border-amber-500/40 bg-amber-500/10 text-[11px] text-amber-200 font-mono";
        lead.innerHTML = `<span class="font-bold">OBSERVED LEAD — NOT ATTRIBUTED:</span> ${observedLead.vasp_name} scored ${observedLead.confidence_score}% (below the 40% qualification threshold). No preservation or disclosure request is available on this lead alone.`;
        vaspChain.parentElement.parentElement.appendChild(lead);
    }
    
    // FIU Badge
    const fiuBadge = document.getElementById("fiuBadge");
    if (fiuBadge) {
        if (attr.primary_vasp && attr.primary_vasp.fiu_ind_registered) {
            fiuBadge.className = "px-2.5 py-0.5 text-[10px] font-bold rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-mono";
            fiuBadge.innerText = "FIU-IND Registered";
        } else {
            fiuBadge.className = "px-2.5 py-0.5 text-[10px] font-bold rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/40 font-mono";
            fiuBadge.innerText = "Foreign Exchange";
        }
    }

    // Risk Assessment Badge
    const riskBadge = document.getElementById("riskLevelBadge");
    if (riskBadge) {
        if (attr.confidence_score >= 80) {
            riskBadge.className = "px-2 py-0.5 rounded-lg bg-rose-500/20 text-rose-300 border border-rose-500/40 font-bold text-[11px] inline-flex items-center gap-1";
            riskBadge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse"></span> HIGH RISK (${Math.round(attr.confidence_score)}/100)`;
        } else if (attr.confidence_score >= 60) {
            riskBadge.className = "px-2 py-0.5 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold text-[11px] inline-flex items-center gap-1";
            riskBadge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> MEDIUM RISK (${Math.round(attr.confidence_score)}/100)`;
        } else {
            riskBadge.className = "px-2 py-0.5 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold text-[11px] inline-flex items-center gap-1";
            riskBadge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> LOW RISK (${Math.round(attr.confidence_score)}/100)`;
        }
    }

    // Populate 4 Explainability Factors ("Why This Attribution?")
    const expContainer = document.getElementById("explainabilityList");
    if (expContainer && attr.explainability) {
        expContainer.innerHTML = "";
        attr.explainability.forEach(factor => {
            const item = document.createElement("div");
            item.className = "p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs";
            item.innerHTML = `
                <div class="flex items-center justify-between font-bold text-slate-200">
                    <span class="flex items-center gap-1.5 text-emerald-400">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"></path></svg>
                        ${factor.title}
                    </span>
                    <span class="text-cyan-400 font-mono text-[11px] font-bold">${Math.round(factor.score * 100)}% Match</span>
                </div>
                <div class="text-slate-300 mt-1 font-medium">${factor.description}</div>
                <div class="text-[11px] text-slate-400 mt-0.5 font-mono">Proof: ${factor.evidence}</div>
            `;
            expContainer.appendChild(item);
        });
    }

    // Synchronize 8-Pillar Intelligence Matrix
    const intel = (attr && attr.intelligence_sources) ? attr.intelligence_sources : (state.traceData ? state.traceData.intelligence_sources : null);
    if (intel) {
        const bTronGrid = document.getElementById("badgeTronGrid");
        if (bTronGrid && intel.source_1_trongrid) {
            bTronGrid.innerText = `${intel.source_1_trongrid.api} (${intel.source_1_trongrid.status})`;
            bTronGrid.className = intel.source_1_trongrid.status === "ACTIVE" ? "text-emerald-400 font-bold" : "text-cyan-300 font-bold";
        }

        const bEtherscan = document.getElementById("badgeEtherscan");
        if (bEtherscan && intel.source_2_etherscan) {
            bEtherscan.innerText = `${intel.source_2_etherscan.api} (${intel.source_2_etherscan.status})`;
            bEtherscan.className = intel.source_2_etherscan.status === "ACTIVE" ? "text-emerald-400 font-bold" : "text-cyan-300 font-bold";
        }

        const bBitquery = document.getElementById("badgeBitquery");
        if (bBitquery && intel.source_3_bitquery) {
            bBitquery.innerText = intel.source_3_bitquery.cluster_id || "Bitquery Verified";
            bBitquery.className = "text-cyan-300 font-bold";
        }

        const bTronscan = document.getElementById("badgeTronscan");
        if (bTronscan && intel.source_4_tronscan) {
            bTronscan.innerText = intel.source_4_tronscan.label_tag || "TRONSCAN Verified";
            bTronscan.className = "text-cyan-300 font-bold";
        }

        const bFiuReg = document.getElementById("badgeFiuReg");
        if (bFiuReg && intel.source_5_fiu_ind) {
            if (intel.source_5_fiu_ind.fiu_ind_registered) {
                bFiuReg.innerText = `Reporting Entity #${intel.source_5_fiu_ind.registration_number || '042'}`;
                bFiuReg.className = "text-emerald-400 font-bold";
            } else {
                bFiuReg.innerText = "Foreign VASP (Non-Reg)";
                bFiuReg.className = "text-amber-400 font-bold";
            }
        }

        const bOfac = document.getElementById("badgeOfac");
        if (bOfac && intel.source_6_ofac_sdn) {
            if (intel.source_6_ofac_sdn.is_sanctioned) {
                bOfac.innerText = "⚠️ SANCTIONED (SDN MATCH)";
                bOfac.className = "text-rose-400 font-bold animate-pulse";
            } else {
                bOfac.innerText = "CLEAN (Passed SDN Check)";
                bOfac.className = "text-emerald-400 font-bold";
            }
        }

        const bChainabuse = document.getElementById("badgeChainabuse");
        if (bChainabuse && intel.source_7_chainabuse) {
            if (intel.source_7_chainabuse.scam_reports_count > 0) {
                bChainabuse.innerText = `Flagged (${intel.source_7_chainabuse.scam_reports_count} Reports)`;
                bChainabuse.className = "text-amber-400 font-bold";
            } else {
                bChainabuse.innerText = "Clean (0 Reports)";
                bChainabuse.className = "text-emerald-400 font-bold";
            }
        }

        const bPostgres = document.getElementById("badgePostgres");
        if (bPostgres && intel.source_8_postgres) {
            bPostgres.innerText = `${intel.source_8_postgres.engine} (CCTNS Synced)`;
            bPostgres.className = "text-cyan-300 font-bold";
        }
    }
}

function renderActionEligibility(eligibility, suggestedAction) {
    const banner = document.getElementById("actionEligibilityBanner");
    const actionBadge = document.getElementById("recommendedActionBadge");
    const actionText = document.getElementById("recommendedActionText");
    const sahyogButton = document.getElementById("btnSahyog");
    const eligible = Boolean(eligibility?.eligible_for_dispatch);
    const scope = eligibility?.examined_hop_scope || 0;
    const reason = eligibility?.reason || "Evidence eligibility was not returned.";

    if (banner) {
        banner.className = eligible
            ? "mt-3 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/40 text-xs font-mono text-emerald-200"
            : "mt-3 p-3 rounded-xl bg-amber-500/10 border border-amber-500/40 text-xs font-mono text-amber-100";
        banner.innerText = eligible
            ? `VERIFIED VASP REACHED — REVIEW REQUIRED. ${reason}`
            : `UNRESOLVED WITHIN ${scope}-HOP EVIDENCE SCOPE — DEEP TRACE REQUIRED. ${reason}`;
    }
    if (actionBadge) actionBadge.innerText = eligible ? "🟢 Reviewable Draft" : "🟠 Deep Trace Required";
    if (actionText) actionText.innerText = eligible
        ? "A connected verified VASP endpoint was found. An investigator may review the draft; no action is automatic."
        : "No VASP freeze or disclosure draft is available. Preserve evidence and expand only the highest-priority unresolved branches.";
    if (sahyogButton) {
        sahyogButton.disabled = !eligible;
        sahyogButton.className = eligible
            ? "py-2.5 px-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow text-center flex items-center justify-center gap-1.5 cursor-pointer"
            : "py-2.5 px-2 rounded-xl bg-slate-700 text-slate-400 font-bold text-xs shadow text-center flex items-center justify-center gap-1.5 cursor-not-allowed disabled:opacity-70";
        sahyogButton.title = eligible ? "Open reviewable SAHYOG draft" : "Blocked until a verified VASP endpoint meets the evidence threshold";
    }
}

// Render Cross-Case Intelligence Alert Banner
function renderCrossCaseAlert(alert) {
    const alertBox = document.getElementById("crossCaseAlertBox");
    if (!alertBox) return;

    if (alert && alert.has_shared_infrastructure) {
        alertBox.classList.remove("hidden");
        const sharedWallet = document.getElementById("crossCaseSharedWallet");
        if (sharedWallet) sharedWallet.innerText = alert.shared_wallet_address;
        
        const linkedCasesList = document.getElementById("crossCaseLinkedCases");
        if (linkedCasesList && alert.linked_case_titles) {
            linkedCasesList.innerHTML = alert.linked_case_titles.map(t => `<li class="text-amber-200 font-mono text-[11px] font-bold">• ${t}</li>`).join("");
        }
        
        const crossNotes = document.getElementById("crossCaseNotes");
        if (crossNotes) crossNotes.innerText = "This exact same middleman wallet was recorded in Mumbai Cyber Crime Case #101! Indicates a shared criminal network.";
    } else {
        alertBox.classList.add("hidden");
    }
}

// Render Evidence Hash Stamp
function renderEvidenceSeal(seal) {
    if (!seal) return;
    const hashDisp = document.getElementById("evidenceHashDisplay");
    if (hashDisp && seal.sha256_hash) {
        hashDisp.innerText = `${seal.sha256_hash.slice(0, 16)}...${seal.sha256_hash.slice(-8)}`;
    }
    const tsDisp = document.getElementById("evidenceTimestamp");
    if (tsDisp && seal.timestamp) {
        tsDisp.innerText = seal.timestamp;
    }
}

// Node Detail Inspector Drawer
function showNodeInspector(node) {
    const drawer = document.getElementById("nodeInspectorDrawer");
    drawer.classList.remove("hidden");
    
    document.getElementById("inspectNodeId").innerText = node.id;
    document.getElementById("inspectNodeType").innerText = node.label;
    document.getElementById("inspectNodeBalance").innerText = node.balance || "0 USDT";
    document.getElementById("inspectNodeRisk").innerText = `${node.risk_score}/100 (${node.risk_level})`;
    
    const tagsContainer = document.getElementById("inspectNodeTags");
    tagsContainer.innerHTML = (node.tags || []).map(t => `<span class="px-2 py-0.5 text-[10px] bg-slate-800 border border-slate-700 text-cyan-300 rounded font-mono">${t}</span>`).join(" ");
}

function hideNodeInspector() {
    document.getElementById("nodeInspectorDrawer").classList.add("hidden");
}

// ================= SAHYOG WORKFLOW (MODAL 1) =================

function openSahyogModal() {
    if (!state.isTraced || !state.traceData) {
        alert("⚠️ Please click '▶ ANALYZE WALLET (RUN TRACE)' on the left first to trace fund movements and generate the freezing notice.");
        return;
    }

    if (!state.traceData.action_eligibility?.eligible_for_dispatch) {
        alert("SAHYOG dispatch is blocked: no connected, verified VASP endpoint met the evidence threshold. Preserve the evidence and expand the trace.");
        return;
    }

    const req = state.traceData.sahyog_request;
    const caseMeta = state.traceData.case_metadata;

    document.getElementById("sahyogReqId").innerText = req.request_id;
    document.getElementById("sahyogCaseId").innerText = req.case_id;
    document.getElementById("sahyogFIR").innerText = caseMeta.fir_number;
    document.getElementById("sahyogPoliceStation").innerText = caseMeta.police_station;
    document.getElementById("sahyogVASP").innerText = req.vasp_name;
    document.getElementById("sahyogNodalEmail").innerText = req.fiu_nodal_officer;
    document.getElementById("sahyogTargetWallet").innerText = req.target_wallet;
    document.getElementById("sahyogAmountCrypto").innerText = req.crypto_amount;
    document.getElementById("sahyogAmountINR").innerText = req.inr_equivalent;
    document.getElementById("sahyogLegalSection").innerText = req.legal_section;

    document.getElementById("sahyogDispatchStatusBox").classList.add("hidden");
    document.getElementById("btnDispatchSahyog").disabled = false;
    document.getElementById("btnDispatchSahyog").innerText = "🚀 Review & Approve (Submit Notice)";

    document.getElementById("modalSahyog").classList.remove("hidden");
}

function closeSahyogModal() {
    document.getElementById("modalSahyog").classList.add("hidden");
}

// Simulate SAHYOG API Dispatch
async function dispatchSahyog() {
    const btn = document.getElementById("btnDispatchSahyog");
    btn.innerHTML = `<svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-slate-950 inline" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Submitting to SAHYOG Gateway...`;
    btn.disabled = true;

    try {
        const res = await fetch("/api/sahyog/dispatch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(state.traceData.sahyog_request)
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || "Dispatch was blocked by the evidence gate.");

        const statusBox = document.getElementById("sahyogDispatchStatusBox");
        statusBox.classList.remove("hidden");
        document.getElementById("sahyogReceiptToken").innerText = result.sahyog_receipt_token;
        document.getElementById("sahyogVaspTicket").innerText = result.vasp_acknowledgment.compliance_ticket_id;
        document.getElementById("sahyogVaspAction").innerText = "Draft received by the simulated nodal desk; legal authorization remains required.";

        btn.innerHTML = `✅ Draft Submitted for Legal Review`;
    } catch (err) {
        console.error("Dispatch failed", err);
        btn.disabled = false;
        btn.innerText = "Retry Notice";
    }
}

// ================= OFFICIAL POLICE REPORT (MODAL 2) =================

function openReportModal() {
    if (!state.isTraced || !state.traceData) {
        alert("⚠️ Please click '▶ ANALYZE WALLET (RUN TRACE)' on the left first to trace on-chain transactions and compile the forensic report.");
        return;
    }

    const meta = state.traceData.case_metadata;
    const attr = state.traceData.attribution;
    const seal = state.traceData.evidence_seal;
    const edges = state.traceData.graph.edges || [];
    const crossCase = state.traceData.cross_case_alert;

    // 1. Header Information
    document.getElementById("repCaseId").innerText = meta.case_id;
    document.getElementById("repTitle").innerText = meta.title;
    document.getElementById("repFIR").innerText = meta.fir_number;
    document.getElementById("repStation").innerText = meta.police_station;
    document.getElementById("repOfficer").innerText = meta.investigating_officer;
    document.getElementById("repAmount").innerText = `₹${meta.amount_inr.toLocaleString()} (${attr.total_volume_tracked} ${meta.token})`;

    // 2. Step-by-Step Transaction Table
    const tbody = document.getElementById("repTableBody");
    tbody.innerHTML = edges.map((e, idx) => {
        let role = `Transfer to Middleman ${e.hop}`;
        if (e.is_sweep) role = "Consolidation to Exchange Main Vault";
        else if (e.hop === edges.length - 1) role = "Deposit to Exchange User Account";

        return `
            <tr class="border-b border-slate-300">
                <td class="p-2 border border-slate-300 font-mono font-bold">Hop #${e.hop}</td>
                <td class="p-2 border border-slate-300 font-mono text-[11px]">${e.source.slice(0, 8)}...${e.source.slice(-6)}</td>
                <td class="p-2 border border-slate-300 font-mono text-[11px]">${e.target.slice(0, 8)}...${e.target.slice(-6)}</td>
                <td class="p-2 border border-slate-300 font-mono font-bold text-right">${e.amount.toLocaleString()} ${e.token}</td>
                <td class="p-2 border border-slate-300 text-[11px]">${role}</td>
            </tr>
        `;
    }).join("");

    // 3. VASP Attribution Findings
    document.getElementById("repVASP").innerText = attr.primary_vasp.vasp_name;
    document.getElementById("repConfidenceBadge").innerText = `${attr.confidence_score}% High Confidence`;
    document.getElementById("repDeposit").innerText = attr.primary_vasp.deposit_address;
    document.getElementById("repReason").innerText = `${attr.flow_percentage}% of stolen funds (${attr.volume_to_vasp} ${meta.token}) reached ${attr.primary_vasp.vasp_name} across ${attr.total_hops} transfers in under 45 minutes.`;

    // 4. Cross-Case Syndicate Link
    const syndicateBox = document.getElementById("repSyndicateBox");
    if (crossCase && crossCase.has_shared_infrastructure) {
        syndicateBox.classList.remove("hidden");
        document.getElementById("repSyndicateNotes").innerText = `Middleman Wallet (${crossCase.shared_wallet_address}) was previously identified in ${crossCase.linked_case_titles[0] || 'Case #101'}. Indicates an active shared criminal syndicate.`;
    } else {
        syndicateBox.classList.add("hidden");
    }

    // 5. Section 65B Seal
    document.getElementById("repHonorSeal").innerText = seal.sha256_hash;
    document.getElementById("repTimestamp").innerText = seal.timestamp;

    document.getElementById("modalReport").classList.remove("hidden");
}

function closeReportModal() {
    document.getElementById("modalReport").classList.add("hidden");
}

// ================= SHA-256 HASH VERIFIER (MODAL 3) =================

function openVerifierModal() {
    if (state.traceData) {
        document.getElementById("verifyInputHash").value = state.traceData.evidence_seal.sha256_hash;
    }
    document.getElementById("verifyResultBox").classList.add("hidden");
    document.getElementById("modalVerifier").classList.remove("hidden");
}

function closeVerifierModal() {
    document.getElementById("modalVerifier").classList.add("hidden");
}

// Execute Live Hash Verification
async function verifySubmittedHash() {
    const inputHash = document.getElementById("verifyInputHash").value.trim();
    const expectedHash = state.traceData ? state.traceData.evidence_seal.sha256_hash : inputHash;

    const res = await fetch("/api/evidence/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            submitted_hash: inputHash,
            expected_hash: expectedHash
        })
    });
    const data = await res.json();

    const resultBox = document.getElementById("verifyResultBox");
    resultBox.classList.remove("hidden");
    
    if (data.is_valid) {
        resultBox.className = "mt-4 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/40 text-emerald-300 text-xs font-mono";
        resultBox.innerHTML = `
            <div class="flex items-center gap-2 font-bold text-sm text-emerald-400">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                REPORT INTEGRITY VERIFIED (UNMODIFIED)
            </div>
            <p class="mt-1 text-slate-300 font-sans">The evidence and transaction records have NOT been modified or tampered with.</p>
            <div class="mt-2 font-mono text-[11px] text-emerald-200/80">Courtroom admissible under Section 63 BSA 2023 [Schedule Two-Signature Format] (formerly Sec 65B IEA).</div>
        `;
    } else {
        resultBox.className = "mt-4 p-4 rounded-xl bg-rose-500/10 border border-rose-500/40 text-rose-300 text-xs font-mono";
        resultBox.innerHTML = `
            <div class="flex items-center gap-2 font-bold text-sm text-rose-400">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                INTEGRITY CHECK FAILED: TAMPERED EVIDENCE
            </div>
            <p class="mt-1 text-slate-300 font-sans">${data.message}</p>
        `;
    }
}

// Copy helper
function copyText(elemId) {
    const text = document.getElementById(elemId).value || document.getElementById(elemId).innerText;
    navigator.clipboard.writeText(text);
    alert("Copied: " + text);
}

// ================= 1930 NCRP LIVE INTAKE WEBHOOK SIMULATOR =================
async function simulate1930NCRPWebhook() {
    // 1. Show notification toast simulating incoming NCRP / 1930 cyber helpline alert
    const toast = document.createElement("div");
    toast.className = "fixed top-5 right-5 z-50 p-4 rounded-2xl bg-[#0b1120]/95 border-2 border-rose-500 text-white shadow-2xl backdrop-blur-md max-w-md font-mono transition-all transform duration-300";
    toast.innerHTML = `
        <div class="flex items-start gap-3">
            <div class="p-2 rounded-xl bg-rose-500/20 text-rose-400 text-lg">🚨</div>
            <div class="flex-1">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-black text-rose-400 uppercase tracking-wide">LIVE 1930 NCRP INTAKE</span>
                    <span class="text-[10px] text-slate-400 font-bold">JUST NOW</span>
                </div>
                <div class="text-xs font-bold text-white mt-1">FIR/2026/CY-JPR/709 • Jaipur Cyber Cell</div>
                <div class="text-[11px] text-slate-300 mt-0.5">Victim: Dr. Amit Mehra • ₹2,10,000 USDT TRC-20</div>
                <div class="text-[10px] text-cyan-300 mt-1 font-mono break-all">Suspect: TJ9kLpBw81xPqrN4x78G44mX2e1Vb889Zq</div>
                <div class="mt-2 text-[10px] text-emerald-400 font-bold flex items-center gap-1">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                    Auto-routing case to VASP TRACE Workbench...
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4500);

    // 2. Select Case 147, switch to Screen 3, and auto run trace
    await selectCase("CASE-147", false);
    goToScreen("ANALYSIS");
    setTimeout(() => {
        triggerTrace();
    }, 300);
}

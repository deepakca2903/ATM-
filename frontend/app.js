// ATM Account Management Front-End Application Logic (October 2026)

const AppState = {
    activeAccount: null,
    enteredPin: "",
    pinPendingAction: null, // "MENU" or custom
    accounts: [],
    systemHealth: null,
    singleAgentHistory: []
};

// Web Audio API Beep Generator for Tactile ATM Feedback
function playATMBeep(freq = 800, duration = 0.08) {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = "sine";
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + duration);
    } catch (e) {
        // AudioContext disabled or unsupported in browser
    }
}

// ==========================================
// INITIALIZATION
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
    initNavigationTabs();
    initKeypad();
    initKioskActions();
    initAccountManagement();
    initSingleAgentChat();
    initMultiAgentVisualizer();
    initSettings();
    loadSystemHealth();
    loadAccounts();
});

// Navigation Tabs
function initNavigationTabs() {
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

            tab.classList.add("active");
            const targetId = tab.getAttribute("data-target");
            const pane = document.getElementById(targetId);
            if (pane) pane.classList.add("active");
        });
    });
}

// System Health
async function loadSystemHealth() {
    try {
        const res = await fetch("/api/health");
        const data = await res.json();
        AppState.systemHealth = data;

        const dbLabel = document.getElementById("db-name-label");
        if (dbLabel) dbLabel.textContent = `DB: ${data.database}`;

        const aiLabel = document.getElementById("ai-name-label");
        if (aiLabel) {
            aiLabel.textContent = data.llm_key_configured 
                ? `AI: ${data.llm_model} (Live)` 
                : `AI: Simulation Engine`;
        }

        const diagDb = document.getElementById("diag-db-engine");
        if (diagDb) diagDb.textContent = data.database;

        const modeBadge = document.getElementById("single-agent-mode-badge");
        if (modeBadge) {
            modeBadge.textContent = data.llm_key_configured ? `Live: ${data.llm_model}` : "Simulation Mode";
        }
    } catch (e) {
        console.error("Health check error:", e);
    }
}

// Load Accounts
async function loadAccounts() {
    try {
        const res = await fetch("/api/accounts");
        const data = await res.json();
        AppState.accounts = data.accounts || [];

        renderKioskAccountDropdown();
        renderAccountsTable(AppState.accounts);
        renderQuickDemoAccounts();
        renderMultiAgentAccountsDropdown();
    } catch (e) {
        console.error("Failed to load accounts:", e);
    }
}

// ==========================================
// ATM KIOSK LOGIC
// ==========================================
function setScreen(screenId) {
    document.querySelectorAll(".screen-view").forEach(s => s.classList.remove("active"));
    const target = document.getElementById(screenId);
    if (target) target.classList.add("active");
}

function renderKioskAccountDropdown() {
    const select = document.getElementById("kiosk-account-select");
    if (!select) return;
    select.innerHTML = AppState.accounts.length === 0 
        ? '<option value="">No accounts found</option>' 
        : '<option value="">-- Choose Account Card --</option>';

    AppState.accounts.forEach(acc => {
        const opt = document.createElement("option");
        opt.value = acc.account_number;
        opt.textContent = `#${acc.account_number} - ${acc.customer_name} (₹${acc.balance.toLocaleString('en-IN')}, ${acc.account_type})`;
        select.appendChild(opt);
    });
}

function renderQuickDemoAccounts() {
    const container = document.getElementById("quick-accounts-list");
    if (!container) return;
    container.innerHTML = "";

    if (AppState.accounts.length === 0) {
        container.innerHTML = '<p class="hint-text">No accounts registered.</p>';
        return;
    }

    AppState.accounts.slice(0, 4).forEach(acc => {
        const btn = document.createElement("button");
        btn.className = "quick-acc-btn";
        btn.innerHTML = `
            <span><strong>#${acc.account_number}</strong> (${acc.customer_name})</span>
            <span>₹${acc.balance.toLocaleString('en-IN')}</span>
        `;
        btn.addEventListener("click", () => {
            selectAndInsertAccount(acc.account_number);
        });
        container.appendChild(btn);
    });
}

function selectAndInsertAccount(accountNumber) {
    const acc = AppState.accounts.find(a => a.account_number === parseInt(accountNumber));
    if (!acc) return;

    AppState.activeAccount = acc;
    AppState.enteredPin = "";
    updatePinDots();

    // Visual Card Slot activation
    const slot = document.getElementById("card-slot-opening");
    if (slot) slot.classList.add("active");
    playATMBeep(900, 0.15);

    // Update Status Pill
    const pill = document.getElementById("active-acc-display");
    if (pill) pill.textContent = `#${acc.account_number} (${acc.customer_name})`;

    // Screen transition to PIN entry
    const pinAcc = document.getElementById("pin-screen-acc");
    const pinUser = document.getElementById("pin-screen-user");
    if (pinAcc) pinAcc.textContent = acc.account_number;
    if (pinUser) pinUser.textContent = acc.customer_name;
    const pinErr = document.getElementById("pin-error-msg");
    if (pinErr) pinErr.textContent = "";

    setScreen("screen-enter-pin");
}

function ejectCard() {
    AppState.activeAccount = null;
    AppState.enteredPin = "";
    updatePinDots();

    const slot = document.getElementById("card-slot-opening");
    if (slot) slot.classList.remove("active");

    const pill = document.getElementById("active-acc-display");
    if (pill) pill.textContent = "No Card Inserted";

    playATMBeep(400, 0.2);
    setScreen("screen-welcome");
    printReceipt({
        title: "CARD EJECTED",
        bodyHtml: "<p>Your card has been safely ejected.</p><p>Please take your card.</p>"
    });
}

// PIN & Keypad
function updatePinDots() {
    const dots = document.querySelectorAll("#pin-dots .dot-slot");
    dots.forEach((dot, idx) => {
        if (idx < AppState.enteredPin.length) {
            dot.classList.add("filled");
        } else {
            dot.classList.remove("filled");
        }
    });
}

function initKeypad() {
    const keys = document.querySelectorAll(".keypad-grid .key-btn");
    keys.forEach(btn => {
        btn.addEventListener("click", () => {
            const key = btn.getAttribute("data-key");
            handleKeypadPress(key);
        });
    });
}

function handleKeypadPress(key) {
    playATMBeep(1000, 0.05);

    // If currently on PIN entry screen
    const pinScreen = document.getElementById("screen-enter-pin");
    const isPinActive = pinScreen && pinScreen.classList.contains("active");

    if (isPinActive) {
        if (key >= "0" && key <= "9") {
            if (AppState.enteredPin.length < 4) {
                AppState.enteredPin += key;
                updatePinDots();
                if (AppState.enteredPin.length === 4) {
                    // Auto-focus or allow user to click submit
                }
            }
        } else if (key === "CLEAR") {
            AppState.enteredPin = "";
            updatePinDots();
        } else if (key === "CANCEL") {
            ejectCard();
        } else if (key === "ENTER") {
            submitPinAuth();
        } else if (key === "HELP") {
            alert("Educational ATM Hint: The default PIN for existing demo account 123456789 is 1234.");
        }
    } else {
        // If on other screens, numbers can fill inputs or CANCEL returns to menu
        if (key === "CANCEL") {
            if (AppState.activeAccount) {
                setScreen("screen-menu");
            } else {
                setScreen("screen-welcome");
            }
        }
    }
}

async function submitPinAuth() {
    if (AppState.enteredPin.length !== 4) {
        const pinErr = document.getElementById("pin-error-msg");
        if (pinErr) pinErr.textContent = "Please enter all 4 digits of your PIN.";
        return;
    }

    try {
        const res = await fetch("/api/accounts/balance", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                account_number: AppState.activeAccount.account_number,
                pin: AppState.enteredPin
            })
        });

        const data = await res.json();
        if (!res.ok) {
            const pinErr = document.getElementById("pin-error-msg");
            if (pinErr) pinErr.textContent = data.detail || "Incorrect PIN. Try again.";
            AppState.enteredPin = "";
            updatePinDots();
            playATMBeep(250, 0.3);
            return;
        }

        // Successfully authenticated!
        AppState.activeAccount.balance = data.balance;
        updateKioskMenuHeader();
        setScreen("screen-menu");
        playATMBeep(1200, 0.1);
    } catch (e) {
        console.error("Auth error:", e);
    }
}

function updateKioskMenuHeader() {
    const acc = AppState.activeAccount;
    if (!acc) return;

    const nameEl = document.getElementById("menu-customer-name");
    const metaEl = document.getElementById("menu-acc-meta");
    if (nameEl) nameEl.textContent = acc.customer_name;
    if (metaEl) metaEl.textContent = `Acc #${acc.account_number} (${acc.account_type}) • Balance: ₹${acc.balance.toLocaleString('en-IN')}`;
}

// Kiosk Screen Interactions
function initKioskActions() {
    // Insert card from select
    const btnInsert = document.getElementById("btn-insert-card");
    if (btnInsert) {
        btnInsert.addEventListener("click", () => {
            const sel = document.getElementById("kiosk-account-select");
            if (sel && sel.value) {
                selectAndInsertAccount(sel.value);
            } else {
                alert("Please select an account from the dropdown first.");
            }
        });
    }

    // Cancel PIN
    const btnCancelPin = document.getElementById("btn-cancel-pin");
    if (btnCancelPin) btnCancelPin.addEventListener("click", ejectCard);

    // Submit PIN
    const btnSubmitPin = document.getElementById("btn-submit-pin");
    if (btnSubmitPin) btnSubmitPin.addEventListener("click", submitPinAuth);

    // Eject Card
    const btnEject = document.getElementById("btn-eject-card");
    if (btnEject) btnEject.addEventListener("click", ejectCard);

    // Back to Menu buttons
    document.querySelectorAll(".btn-back-menu").forEach(btn => {
        btn.addEventListener("click", () => {
            updateKioskMenuHeader();
            setScreen("screen-menu");
        });
    });

    // 1. Menu: Check Balance
    const menuBtnBal = document.getElementById("menu-btn-balance");
    if (menuBtnBal) {
        menuBtnBal.addEventListener("click", () => {
            const acc = AppState.activeAccount;
            document.getElementById("display-balance-val").textContent = `₹${acc.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
            document.getElementById("display-balance-acc").textContent = acc.account_number;
            document.getElementById("display-balance-type").textContent = acc.account_type;
            document.getElementById("display-balance-name").textContent = acc.customer_name;
            setScreen("screen-balance");
        });
    }

    // Print Balance Receipt
    const btnPrintBal = document.getElementById("btn-print-balance-receipt");
    if (btnPrintBal) {
        btnPrintBal.addEventListener("click", () => {
            const acc = AppState.activeAccount;
            printReceipt({
                title: "BALANCE INQUIRY",
                bodyHtml: `
                    <div class="receipt-row"><span>Account No:</span><strong>#${acc.account_number}</strong></div>
                    <div class="receipt-row"><span>Customer:</span><strong>${acc.customer_name}</strong></div>
                    <div class="receipt-row"><span>Type:</span><strong>${acc.account_type}</strong></div>
                    <div class="receipt-row"><span>Available Balance:</span><strong>₹${acc.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong></div>
                `
            });
        });
    }

    // 2. Menu: Deposit
    const menuBtnDep = document.getElementById("menu-btn-deposit");
    if (menuBtnDep) {
        menuBtnDep.addEventListener("click", () => {
            document.getElementById("deposit-amount-input").value = "";
            document.getElementById("deposit-error-msg").textContent = "";
            setScreen("screen-deposit");
        });
    }

    // Deposit Quick Tags
    document.querySelectorAll(".quick-amount-tags .btn-tag").forEach(tag => {
        tag.addEventListener("click", () => {
            const val = parseFloat(tag.getAttribute("data-val"));
            const input = document.getElementById("deposit-amount-input");
            const current = parseFloat(input.value) || 0;
            input.value = current + val;
        });
    });

    // Confirm Deposit
    const btnConfirmDep = document.getElementById("btn-confirm-deposit");
    if (btnConfirmDep) {
        btnConfirmDep.addEventListener("click", async () => {
            const input = document.getElementById("deposit-amount-input");
            const amount = parseFloat(input.value);
            const errEl = document.getElementById("deposit-error-msg");

            if (!amount || amount <= 0) {
                errEl.textContent = "Please enter a valid deposit amount greater than zero.";
                return;
            }

            try {
                const res = await fetch("/api/accounts/deposit", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        account_number: AppState.activeAccount.account_number,
                        amount: amount
                    })
                });

                const data = await res.json();
                if (!res.ok) {
                    errEl.textContent = data.detail || "Deposit failed.";
                    return;
                }

                AppState.activeAccount.balance = data.balance;
                await loadAccounts();
                updateKioskMenuHeader();

                printReceipt({
                    title: "CASH DEPOSIT SUCCESSFUL",
                    bodyHtml: `
                        <div class="receipt-row"><span>Account No:</span><strong>#${data.account_number}</strong></div>
                        <div class="receipt-row"><span>Amount Deposited:</span><strong>₹${data.deposited_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong></div>
                        <div class="receipt-row"><span>New Balance:</span><strong>₹${data.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong></div>
                    `
                });

                alert(`Deposit Successful! ₹${amount.toLocaleString('en-IN')} credited.`);
                setScreen("screen-menu");
            } catch (e) {
                errEl.textContent = `Error: ${e.message}`;
            }
        });
    }

    // 3. Menu: Withdraw
    const menuBtnWith = document.getElementById("menu-btn-withdraw");
    if (menuBtnWith) {
        menuBtnWith.addEventListener("click", () => {
            document.getElementById("withdraw-custom-input").value = "";
            document.getElementById("withdraw-error-msg").textContent = "";
            setScreen("screen-withdraw");
        });
    }

    // Fast Cash Buttons
    document.querySelectorAll(".btn-fast-cash").forEach(btn => {
        btn.addEventListener("click", () => {
            const amt = parseFloat(btn.getAttribute("data-amount"));
            executeWithdrawal(amt);
        });
    });

    // Custom Cash Withdraw
    const btnConfirmWith = document.getElementById("btn-confirm-withdraw");
    if (btnConfirmWith) {
        btnConfirmWith.addEventListener("click", () => {
            const input = document.getElementById("withdraw-custom-input");
            const amt = parseFloat(input.value);
            executeWithdrawal(amt);
        });
    }

    // 4. Menu: Change PIN
    const menuBtnPin = document.getElementById("menu-btn-pin");
    if (menuBtnPin) {
        menuBtnPin.addEventListener("click", () => {
            document.getElementById("pin-old-val").value = "";
            document.getElementById("pin-new-val").value = "";
            document.getElementById("pin-confirm-val").value = "";
            document.getElementById("change-pin-error").textContent = "";
            setScreen("screen-change-pin");
        });
    }

    const btnConfirmChangePin = document.getElementById("btn-confirm-change-pin");
    if (btnConfirmChangePin) {
        btnConfirmChangePin.addEventListener("click", async () => {
            const oldPin = document.getElementById("pin-old-val").value.trim();
            const newPin = document.getElementById("pin-new-val").value.trim();
            const confPin = document.getElementById("pin-confirm-val").value.trim();
            const errEl = document.getElementById("change-pin-error");

            if (!oldPin || !newPin || !confPin) {
                errEl.textContent = "All PIN fields are required.";
                return;
            }

            try {
                const res = await fetch("/api/accounts/change-pin", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        account_number: AppState.activeAccount.account_number,
                        old_pin: oldPin,
                        new_pin: newPin,
                        confirm_pin: confPin
                    })
                });

                const data = await res.json();
                if (!res.ok) {
                    errEl.textContent = data.detail || "PIN update failed.";
                    return;
                }

                AppState.enteredPin = newPin;
                alert("PIN changed successfully! Please remember your new 4-digit PIN.");
                setScreen("screen-menu");
            } catch (e) {
                errEl.textContent = `Error: ${e.message}`;
            }
        });
    }

    // 5. Menu: Mini Statement
    const menuBtnHist = document.getElementById("menu-btn-history");
    if (menuBtnHist) {
        menuBtnHist.addEventListener("click", async () => {
            await loadMiniStatement();
            setScreen("screen-history");
        });
    }

    // Print Statement
    const btnPrintStmt = document.getElementById("btn-print-statement-receipt");
    if (btnPrintStmt) {
        btnPrintStmt.addEventListener("click", () => {
            const acc = AppState.activeAccount;
            printReceipt({
                title: "MINI STATEMENT",
                bodyHtml: `
                    <div class="receipt-row"><span>Account No:</span><strong>#${acc.account_number}</strong></div>
                    <div class="receipt-row"><span>Customer:</span><strong>${acc.customer_name}</strong></div>
                    <div class="receipt-row"><span>Balance:</span><strong>₹${acc.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong></div>
                    <hr class="receipt-divider">
                    <p style="font-size:0.7rem;">Recent transactions printed at terminal.</p>
                `
            });
        });
    }

    // 6. Menu: Close Account
    const menuBtnClose = document.getElementById("menu-btn-close");
    if (menuBtnClose) {
        menuBtnClose.addEventListener("click", () => {
            const acc = AppState.activeAccount;
            document.getElementById("close-screen-bal").textContent = `₹${acc.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
            document.getElementById("close-pin-input").value = "";
            document.getElementById("close-confirm-chk").checked = false;
            document.getElementById("close-error-msg").textContent = "";
            setScreen("screen-close-account");
        });
    }

    const btnConfirmClose = document.getElementById("btn-confirm-close-account");
    if (btnConfirmClose) {
        btnConfirmClose.addEventListener("click", async () => {
            const acc = AppState.activeAccount;
            const pinVal = document.getElementById("close-pin-input").value.trim();
            const chkVal = document.getElementById("close-confirm-chk").checked;
            const errEl = document.getElementById("close-error-msg");

            if (!chkVal) {
                errEl.textContent = "You must check the confirmation box.";
                return;
            }

            try {
                const res = await fetch("/api/accounts/close", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        account_number: acc.account_number,
                        pin: pinVal,
                        confirmation: true
                    })
                });

                const data = await res.json();
                if (!res.ok) {
                    errEl.textContent = data.detail || "Account closure failed.";
                    return;
                }

                alert(`Account #${acc.account_number} closed successfully!`);
                ejectCard();
                await loadAccounts();
            } catch (e) {
                errEl.textContent = `Error: ${e.message}`;
            }
        });
    }
}

async function executeWithdrawal(amount) {
    const errEl = document.getElementById("withdraw-error-msg");
    if (!amount || amount <= 0) {
        errEl.textContent = "Please select or enter a valid withdrawal amount.";
        return;
    }

    try {
        const res = await fetch("/api/accounts/withdraw", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                account_number: AppState.activeAccount.account_number,
                pin: AppState.enteredPin,
                amount: amount
            })
        });

        const data = await res.json();
        if (!res.ok) {
            errEl.textContent = data.detail || "Withdrawal failed.";
            playATMBeep(200, 0.25);
            return;
        }

        // Success!
        AppState.activeAccount.balance = data.balance;
        await loadAccounts();
        updateKioskMenuHeader();

        // Animate Cash Slot
        const cashSlot = document.getElementById("cash-slot-opening");
        if (cashSlot) {
            cashSlot.classList.add("active");
            setTimeout(() => cashSlot.classList.remove("active"), 4000);
        }

        // Render Dispense Screen
        document.getElementById("dispensed-amount-val").textContent = `₹${data.withdrawn_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
        document.getElementById("dispense-rem-balance").textContent = `₹${data.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

        const denomsList = document.getElementById("denominations-list");
        denomsList.innerHTML = "";
        for (const [denom, count] of Object.entries(data.denominations)) {
            const pill = document.createElement("span");
            pill.className = "denom-pill";
            pill.textContent = `${count} x ${denom}`;
            denomsList.appendChild(pill);
        }

        setScreen("screen-dispense-success");

        // Print Receipt Automatically
        printReceipt({
            title: "CASH WITHDRAWAL RECEIPT",
            bodyHtml: `
                <div class="receipt-row"><span>Account No:</span><strong>#${data.account_number}</strong></div>
                <div class="receipt-row"><span>Amount Withdrawn:</span><strong>₹${data.withdrawn_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong></div>
                <div class="receipt-row"><span>Available Balance:</span><strong>₹${data.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong></div>
                <div class="receipt-row"><span>Dispensed:</span><strong>${Object.entries(data.denominations).map(([k,v]) => `${v}x${k}`).join(", ")}</strong></div>
            `
        });
    } catch (e) {
        errEl.textContent = `Error: ${e.message}`;
    }
}

async function loadMiniStatement() {
    const tbody = document.getElementById("kiosk-history-tbody");
    tbody.innerHTML = '<tr><td colspan="4">Loading history...</td></tr>';

    try {
        const res = await fetch(`/api/accounts/${AppState.activeAccount.account_number}/transactions?limit=6`);
        const data = await res.json();
        const txs = data.transactions || [];

        if (txs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4">No transactions recorded yet.</td></tr>';
            return;
        }

        tbody.innerHTML = "";
        txs.forEach(t => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${t.transaction_type}</strong></td>
                <td>₹${t.amount.toLocaleString('en-IN')}</td>
                <td>₹${t.balance_after.toLocaleString('en-IN')}</td>
                <td><small>${t.created_at.slice(0, 19)}</small></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="4" class="error-text">Failed to load history: ${e.message}</td></tr>`;
    }
}

// Thermal Receipt Generator
function printReceipt({ title, bodyHtml }) {
    const paper = document.getElementById("receipt-body");
    if (!paper) return;

    const timestamp = new Date().toLocaleString();
    paper.innerHTML = `
        <div style="text-align:center; font-weight:700; margin-bottom:8px;">${title}</div>
        <div class="receipt-row"><span>DATE/TIME:</span><span>${timestamp}</span></div>
        <hr class="receipt-divider">
        ${bodyHtml}
    `;

    // Animate receipt printer slot
    const slot = document.getElementById("receipt-slot-opening");
    if (slot) {
        slot.classList.add("active");
        setTimeout(() => slot.classList.remove("active"), 2000);
    }
    playATMBeep(1400, 0.08);
}

// ==========================================
// TAB 2: ACCOUNT MANAGEMENT
// ==========================================
function initAccountManagement() {
    // Form Create Account
    const form = document.getElementById("form-create-account");
    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const feedback = document.getElementById("create-account-feedback");
            feedback.className = "feedback-msg";
            feedback.style.display = "none";

            const accNum = parseInt(document.getElementById("create-acc-num").value);
            const name = document.getElementById("create-acc-name").value.trim();
            const accType = document.getElementById("create-acc-type").value;
            const pin = document.getElementById("create-acc-pin").value.trim();
            const balance = parseFloat(document.getElementById("create-acc-bal").value) || 0.0;

            try {
                const res = await fetch("/api/accounts", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        account_number: accNum,
                        customer_name: name,
                        account_type: accType,
                        pin: pin,
                        balance: balance
                    })
                });

                const data = await res.json();
                if (!res.ok) {
                    feedback.className = "feedback-msg error";
                    feedback.textContent = data.detail || "Failed to create account.";
                    return;
                }

                feedback.className = "feedback-msg success";
                feedback.textContent = `Account #${data.account_number} created successfully for ${data.customer_name}!`;
                form.reset();
                await loadAccounts();
            } catch (err) {
                feedback.className = "feedback-msg error";
                feedback.textContent = `Error: ${err.message}`;
            }
        });
    }

    // Search Account
    const searchInput = document.getElementById("search-input");
    const btnSearch = document.getElementById("btn-search-trigger");
    const btnRefresh = document.getElementById("btn-refresh-accounts");

    if (btnSearch) {
        btnSearch.addEventListener("click", () => performSearch(searchInput.value));
    }
    if (searchInput) {
        searchInput.addEventListener("keyup", (e) => {
            if (e.key === "Enter") performSearch(searchInput.value);
        });
    }
    if (btnRefresh) {
        btnRefresh.addEventListener("click", () => {
            searchInput.value = "";
            loadAccounts();
        });
    }
}

async function performSearch(query) {
    try {
        const url = query ? `/api/accounts/search?query=${encodeURIComponent(query)}` : "/api/accounts";
        const res = await fetch(url);
        const data = await res.json();
        renderAccountsTable(data.accounts || []);
    } catch (e) {
        console.error("Search failed:", e);
    }
}

function renderAccountsTable(accounts) {
    const tbody = document.getElementById("accounts-table-body");
    if (!tbody) return;

    if (accounts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">No accounts found.</td></tr>';
        return;
    }

    tbody.innerHTML = "";
    accounts.forEach(acc => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>#${acc.account_number}</strong></td>
            <td>${acc.customer_name}</td>
            <td><span class="badge badge-accent">${acc.account_type}</span></td>
            <td><strong style="color:#10b981;">₹${acc.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong></td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="quickSelectAccount(${acc.account_number})">Use in ATM 🏧</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

window.quickSelectAccount = function(accNum) {
    // Switch to Kiosk Tab
    document.querySelector('.nav-tab[data-target="tab-kiosk"]').click();
    selectAndInsertAccount(accNum);
};

// ==========================================
// TAB 3: SINGLE-AGENT AI COPILOT
// ==========================================
function initSingleAgentChat() {
    const form = document.getElementById("single-agent-form");
    const input = document.getElementById("single-agent-input");

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const text = input.value.trim();
            if (!text) return;
            input.value = "";
            await sendSingleAgentMessage(text);
        });
    }

    // Prompt Chips
    document.querySelectorAll(".chip-btn").forEach(chip => {
        chip.addEventListener("click", () => {
            const prompt = chip.getAttribute("data-prompt");
            sendSingleAgentMessage(prompt);
        });
    });
}

async function sendSingleAgentMessage(userText) {
    const container = document.getElementById("single-agent-messages");
    
    // Append User Bubble
    const userBubble = document.createElement("div");
    userBubble.className = "chat-bubble user-bubble";
    userBubble.innerHTML = `<div class="bubble-content">${escapeHtml(userText)}</div>`;
    container.appendChild(userBubble);
    container.scrollTop = container.scrollHeight;

    // Loading Assistant Bubble
    const assistantBubble = document.createElement("div");
    assistantBubble.className = "chat-bubble assistant-bubble";
    assistantBubble.innerHTML = `<div class="bubble-header">🤖 ATM Copilot</div><div class="bubble-content"><em>Thinking & querying banking tools...</em></div>`;
    container.appendChild(assistantBubble);
    container.scrollTop = container.scrollHeight;

    try {
        const payload = {
            message: userText,
            account_number: AppState.activeAccount ? AppState.activeAccount.account_number : null,
            history: AppState.singleAgentHistory
        };

        const res = await fetch("/api/ai/single-agent", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            assistantBubble.querySelector(".bubble-content").textContent = `Error: ${data.detail || "Agent invocation failed."}`;
            return;
        }

        // Render response
        assistantBubble.querySelector(".bubble-content").innerHTML = formatMarkdown(data.response);
        container.scrollTop = container.scrollHeight;

        // Render Tool Calls
        renderToolStream(data.tool_calls || []);

        // Update history
        AppState.singleAgentHistory.push({ role: "user", content: userText });
        AppState.singleAgentHistory.push({ role: "assistant", content: data.response });
    } catch (e) {
        assistantBubble.querySelector(".bubble-content").textContent = `Network error: ${e.message}`;
    }
}

function renderToolStream(toolCalls) {
    const stream = document.getElementById("tool-calls-stream");
    if (!stream) return;

    if (toolCalls.length === 0) return;

    toolCalls.forEach(tc => {
        const card = document.createElement("div");
        card.className = "tool-execution-card";
        card.innerHTML = `
            <div><span class="tool-badge">🔧 Tool Call:</span> <strong>${tc.tool}</strong></div>
            <div class="tool-args">args: ${JSON.stringify(tc.arguments)}</div>
            <div class="tool-output">${JSON.stringify(tc.result, null, 2)}</div>
        `;
        stream.prepend(card);
    });
}

// ==========================================
// TAB 4: MULTI-AGENT RISK & ADVISORY
// ==========================================
function renderMultiAgentAccountsDropdown() {
    const sel = document.getElementById("ma-account-select");
    if (!sel) return;
    sel.innerHTML = "";

    AppState.accounts.forEach(acc => {
        const opt = document.createElement("option");
        opt.value = acc.account_number;
        opt.textContent = `#${acc.account_number} - ${acc.customer_name} (₹${acc.balance.toLocaleString('en-IN')})`;
        sel.appendChild(opt);
    });
}

function initMultiAgentVisualizer() {
    const form = document.getElementById("multi-agent-form");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const accNum = parseInt(document.getElementById("ma-account-select").value);
        const actionType = document.getElementById("ma-action-type").value;
        const amount = parseFloat(document.getElementById("ma-amount-input").value) || 0.0;
        const scenario = document.getElementById("ma-scenario-input").value.trim();

        const btn = document.getElementById("btn-run-multi-agent");
        btn.textContent = "Convening Committee... ⏳";
        btn.disabled = true;

        try {
            const res = await fetch("/api/ai/multi-agent", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    account_number: accNum,
                    action_type: actionType,
                    amount: amount,
                    scenario: scenario
                })
            });

            const data = await res.json();
            btn.textContent = "Convene Multi-Agent Committee 👥";
            btn.disabled = false;

            if (!res.ok) {
                alert(`Multi-Agent committee error: ${data.detail || "Evaluation failed."}`);
                return;
            }

            renderMultiAgentResults(data);
        } catch (err) {
            btn.textContent = "Convene Multi-Agent Committee 👥";
            btn.disabled = false;
            alert(`Network error: ${err.message}`);
        }
    });
}

function renderMultiAgentResults(data) {
    // 1. Concierge
    const conc = data.concierge_agent;
    const concEl = document.getElementById("concierge-content");
    concEl.innerHTML = `
        <p><strong>Decomposed Request:</strong> ${conc.action_requested}</p>
        <p style="margin-top:6px;">${conc.observation}</p>
    `;

    // 2. Security Auditor
    const sec = data.security_agent;
    const secEl = document.getElementById("security-content");
    const reasonsHtml = sec.reasons.map(r => `<li>${r}</li>`).join("");
    secEl.innerHTML = `
        <p><strong>Verdict:</strong> <span class="badge ${sec.verdict === 'APPROVED' ? 'badge-accent' : 'badge-danger'}">${sec.verdict}</span></p>
        <p><strong>Risk Score:</strong> ${sec.risk_score}/100</p>
        <ul style="padding-left:16px; margin-top:6px;">${reasonsHtml}</ul>
    `;

    // 3. Financial Advisor
    const fin = data.financial_agent;
    const finEl = document.getElementById("financial-content");
    const recsHtml = fin.recommendations.map(r => `<li>${r}</li>`).join("");
    finEl.innerHTML = `
        <p><strong>Liquidity Impact:</strong> ${fin.impact_analysis}</p>
        <p style="margin-top:6px;"><strong>Advisory Tips:</strong></p>
        <ul style="padding-left:16px;">${recsHtml}</ul>
    `;

    // 4. Synthesis Consensus
    const syn = data.synthesis;
    const badge = document.getElementById("verdict-badge");
    badge.className = "verdict-badge";
    badge.textContent = syn.final_verdict;

    if (syn.final_verdict === "APPROVED") {
        badge.classList.add("verdict-approved");
    } else if (syn.final_verdict === "CONDITIONAL") {
        badge.classList.add("verdict-conditional");
    } else {
        badge.classList.add("verdict-blocked");
    }

    document.getElementById("composite-risk-val").textContent = `${syn.composite_risk_score}%`;
    document.getElementById("consensus-summary-text").textContent = syn.summary_rationale;
}

// ==========================================
// TAB 5: SETTINGS
// ==========================================
function initSettings() {
    const form = document.getElementById("form-llm-settings");
    if (!form) return;

    // Load initial config
    fetch("/api/ai/config")
        .then(r => r.json())
        .then(cfg => {
            document.getElementById("cfg-base-url").value = cfg.base_url || "";
            document.getElementById("cfg-model-name").value = cfg.model || "";
        })
        .catch(console.error);

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const feedback = document.getElementById("llm-cfg-feedback");
        feedback.className = "feedback-msg";

        const baseUrl = document.getElementById("cfg-base-url").value.trim();
        const model = document.getElementById("cfg-model-name").value.trim();
        const apiKey = document.getElementById("cfg-api-key").value.trim();

        try {
            const res = await fetch("/api/ai/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    base_url: baseUrl,
                    model: model,
                    api_key: apiKey
                })
            });

            const data = await res.json();
            feedback.className = "feedback-msg success";
            feedback.textContent = "AI Configuration saved successfully!";
            await loadSystemHealth();
        } catch (err) {
            feedback.className = "feedback-msg error";
            feedback.textContent = `Failed to save: ${err.message}`;
        }
    });
}

// Utility: Simple Markdown & Escaping
function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function formatMarkdown(text) {
    if (!text) return "";
    let html = escapeHtml(text);
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");
    html = html.replace(/`(.*?)`/g, "<code>$1</code>");
    html = html.replace(/\n\n/g, "<br><br>");
    html = html.replace(/\n- (.*?)/g, "<br>• $1");
    return html;
}

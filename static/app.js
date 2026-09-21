let config = null;
let admin = false;
let mode = "practice";

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function esc(value) {
    return String(value).replace(/[&<>'"]/g, (character) => {
        return {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            "'": "&#39;",
            '"': "&quot;"
        }[character];
    });
}

async function api(url, options = {}) {
    const response = await fetch(url, {
        headers: { "Content-Type": "application/json" },
        ...options
    });

    return response.json();
}

function showPage(id) {
    $$(".page").forEach((page) => {
        page.classList.toggle("active", page.id === id);
    });

    $$(".nav").forEach((button) => {
        button.classList.toggle("active", button.dataset.page === id);
    });

    window.scrollTo({ top: 0, behavior: "smooth" });

    if (id === "admin") {
        renderAdmin();
    }
}

function activity(id) {
    return config.activities.find((item) => item.id === id);
}

function makeChat(target, id) {
    const item = activity(id);
    const container = $(target);

    container.innerHTML = `
        <div class="chat">
            <div class="chat-header">
                <div>
                    <strong>AI Learning Coach — ${esc(item.title)}</strong><br>
                    <small>
                        ${
                            item.type === "assessment"
                                ? "Assessed checkpoint"
                                : "Orientation / practice activity"
                        }
                    </small>
                </div>
                <span class="badge">KNOWLEDGE-GROUNDED SIMULATION</span>
            </div>

            <div class="chat-body" id="body-${id}">
                <div class="bubble ta">${esc(item.prompt)}</div>
            </div>

            <div class="chat-input">
                <textarea
                    id="input-${id}"
                    placeholder="Write your response in your own words..."
                ></textarea>

                <button class="primary" data-send="${id}">Send</button>
            </div>
        </div>
    `;
}

function append(id, who, text) {
    const body = $("#body-" + id);

    body.insertAdjacentHTML(
        "beforeend",
        `<div class="bubble ${who}">${esc(text)}</div>`
    );

    body.scrollTop = body.scrollHeight;
}

async function send(id) {
    const input = $("#input-" + id);
    const message = input.value.trim();

    if (!message) return;

    input.value = "";
    append(id, "student", message);

    const response = await api("/api/chat", {
        method: "POST",
        body: JSON.stringify({
            activity_id: id,
            message: message,
            mode: mode,
            chat_type: "activity"
        })
    });

    append(id, "ta", response.reply || "Prototype error.");
}

function renderWeek() {
    makeChat("#caseChat", "case");
    makeChat("#entryChat", "entry");
    makeChat("#investigationChat", "investigation");
    makeChat("#evidenceChat", "evidence");
    makeChat("#causationChat", "causation");
    makeChat("#critiqueChat", "critique");
    makeChat("#memoChat", "memo");
    makeChat("#reflectionChat", "reflection");
}

function renderGeneral() {
    const container = $("#generalChat");

    container.innerHTML = `
        <div class="chat">
            <div class="chat-header">
                <div>
                    <strong>General Coach</strong><br>
                    <small>Week 3 concept explanations</small>
                </div>
                <span class="badge">KNOWLEDGE-GROUNDED SIMULATION</span>
            </div>

            <div class="chat-body" id="generalBody">
                <div class="bubble ta">
                    Ask a general Week 3 question, such as:
                    “What is diagnostic analytics?”
                    “Why do I need diagnostic analytics?”
                    “What is triangulation?”
                    or “What is the difference between association and causation?”
                </div>
            </div>

            <div class="chat-input">
                <textarea
                    id="generalInput"
                    placeholder="Ask a general Week 3 analytics question..."
                ></textarea>

                <button class="primary" id="generalSend">Send</button>
            </div>
        </div>
    `;

    $("#generalSend").onclick = async () => {
        const input = $("#generalInput");
        const message = input.value.trim();

        if (!message) return;

        input.value = "";

        $("#generalBody").insertAdjacentHTML(
            "beforeend",
            `<div class="bubble student">${esc(message)}</div>`
        );

        const response = await api("/api/chat", {
            method: "POST",
            body: JSON.stringify({
                activity_id: "case",
                message: message,
                mode: "practice",
                chat_type: "general"
            })
        });

        $("#generalBody").insertAdjacentHTML(
            "beforeend",
            `<div class="bubble ta">${esc(
                response.reply || "Prototype error."
            )}</div>`
        );

        $("#generalBody").scrollTop = $("#generalBody").scrollHeight;
    };
}

function renderShell() {
    $("#syllabusRows").innerHTML = config.weeks
        .map((week) => {
            return `
                <tr>
                    <td>${week.week}</td>
                    <td>${week.hours}</td>
                    <td>${esc(week.topic)}</td>
                    <td>${esc(week.document)}</td>
                    <td>${esc(week.ai)}</td>
                </tr>
            `;
        })
        .join("");

    $("#courseCards").innerHTML = config.weeks
        .slice(0, 6)
        .map((week) => {
            return `
                <div class="mini-course">
                    <strong>Week ${week.week}: ${esc(week.topic)}</strong>
                    <small>
                        ${week.week === 3 ? "Available prototype" : "Course shell"}
                    </small>
                </div>
            `;
        })
        .join("");

    $("#assignmentCards").innerHTML = config.activities
        .filter((item) => item.type !== "orientation")
        .map((item) => {
            return `
                <div class="assignment">
                    <div class="type">${esc(item.type)}</div>
                    <h3>${esc(item.title)}</h3>
                    <p>${esc(item.prompt)}</p>
                    <button
                        class="secondary"
                        data-open-activity="${item.id}"
                    >
                        Open in Week 3
                    </button>
                </div>
            `;
        })
        .join("");

    $("#progressList").innerHTML = config.activities
        .map((item, index) => {
            return `
                <div class="course-card">
                    <div class="icon blue">${index + 1}</div>
                    <div>
                        <strong>${esc(item.title)}</strong>
                        <p>
                            ${esc(item.type)} •
                            ${
                                item.type === "orientation"
                                    ? "Not assessed"
                                    : "Checkpoint"
                            }
                        </p>
                    </div>
                    <span class="badge">Not started</span>
                </div>
            `;
        })
        .join("");
}

function renderAdmin() {
    const guard = $("#adminGuard");
    const panel = $("#adminPanel");

    guard.classList.toggle("hidden", admin);
    panel.classList.toggle("hidden", !admin);

    if (!admin) return;

    const selector = $("#activitySelect");

    selector.innerHTML = config.activities
        .map((item) => {
            return `<option value="${item.id}">${esc(item.title)}</option>`;
        })
        .join("");

    loadActivity(selector.value);
    selector.onchange = () => loadActivity(selector.value);
}

function loadActivity(id) {
    const item = activity(id);

    $("#editTitle").value = item.title;
    $("#editPrompt").value = item.prompt;
    $("#editType").value = item.type;
    $("#editCriteria").value = item.criteria.join("\n");
    $("#editCorrect").value = item.responses.correct;
    $("#editIncomplete").value = item.responses.incomplete;
    $("#editDirect").value = item.responses.direct;

    $("#ladderEditor").innerHTML = item.ladder
        .map((text, index) => {
            return `
                <div class="ladder-item">
                    <label>Level ${index}</label>
                    <textarea data-ladder="${index}">${esc(text)}</textarea>
                </div>
            `;
        })
        .join("");
}

async function saveActivity() {
    const item = activity($("#activitySelect").value);

    item.title = $("#editTitle").value;
    item.prompt = $("#editPrompt").value;
    item.type = $("#editType").value;
    item.criteria = $("#editCriteria")
        .value.split("\n")
        .map((value) => value.trim())
        .filter(Boolean);

    item.responses.correct = $("#editCorrect").value;
    item.responses.incomplete = $("#editIncomplete").value;
    item.responses.direct = $("#editDirect").value;
    item.ladder = $$("[data-ladder]").map((element) => element.value);

    const response = await api("/api/config", {
        method: "PUT",
        body: JSON.stringify({ config })
    });

    $("#saveMessage").textContent = response.message || "Saved";

    renderShell();
    renderWeek();
}

function testAdmin() {
    const item = activity($("#activitySelect").value);
    const type = $("#testType").value;

    let reply = "";

    if (type === "correct") {
        reply = item.responses.correct;
    } else if (type === "direct") {
        reply = item.responses.direct;
    } else if (mode === "assessment" && item.type === "assessment") {
        reply =
            "Assessment mode: " +
            item.responses.incomplete +
            " Please revise independently. No hint is given.";
    } else {
        reply =
            item.responses.incomplete +
            "\n\nSupport level 1 — " +
            item.ladder[1];
    }

    $("#testOutput").textContent = reply;
}

async function init() {
    config = await api("/api/config");

    renderShell();
    renderWeek();
    renderGeneral();

    $$(".nav").forEach((button) => {
        button.onclick = () => showPage(button.dataset.page);
    });

    $$("[data-go]").forEach((button) => {
        button.onclick = () => showPage(button.dataset.go);
    });

    document.body.addEventListener("click", (event) => {
        const sendButton = event.target.closest("[data-send]");

        if (sendButton) {
            send(sendButton.dataset.send);
        }

        const activityButton = event.target.closest("[data-open-activity]");

        if (activityButton) {
            showPage("week3");

            setTimeout(() => {
                $("#input-" + activityButton.dataset.openActivity)?.focus();
            }, 300);
        }
    });

    $("#studentBtn").onclick = () => {
        admin = false;
        $("#studentBtn").classList.add("active");
        $("#adminBtn").classList.remove("active");
        $("#modeLabel").textContent = "Student view";
        showPage("dashboard");
    };

    $("#adminBtn").onclick = () => {
        admin = true;
        $("#adminBtn").classList.add("active");
        $("#studentBtn").classList.remove("active");
        $("#modeLabel").textContent = "Admin view";
        showPage("admin");
    };

    $("#modeSelect").onchange = (event) => {
        mode = event.target.value;

        $("#modeText").textContent =
            mode === "practice"
                ? "Practice mode gives targeted scaffolded support only after a student attempt."
                : "Assessment mode pulls the ladder back: the prototype requests an independent revision without instructional hints.";
    };

    $("#saveActivity").onclick = saveActivity;
    $("#runTest").onclick = testAdmin;
}

document.addEventListener("DOMContentLoaded", init);

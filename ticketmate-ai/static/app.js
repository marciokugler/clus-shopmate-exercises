const state = {
  events: [],
  selectedEventId: "",
  city: "",
  genre: "",
  history: [],
  sessionTokens: 0,
};

const els = {
  eventList: document.querySelector("#eventList"),
  cityFilter: document.querySelector("#cityFilter"),
  genreFilter: document.querySelector("#genreFilter"),
  ticketCount: document.querySelector("#ticketCount"),
  budgetInput: document.querySelector("#budgetInput"),
  scenarioSelect: document.querySelector("#scenarioSelect"),
  chatLog: document.querySelector("#chatLog"),
  chatForm: document.querySelector("#chatForm"),
  chatInput: document.querySelector("#chatInput"),
  sessionTokens: document.querySelector("#sessionTokens"),
  lastTokens: document.querySelector("#lastTokens"),
  lastLatency: document.querySelector("#lastLatency"),
  agentTimeline: document.querySelector("#agentTimeline"),
  nimStatus: document.querySelector("#nimStatus"),
  modelName: document.querySelector("#modelName"),
};

function money(value) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

function eventPosterClass(event) {
  return `poster poster-${event.genre.toLowerCase().replace(/[^a-z]/g, "")}`;
}

function filteredEvents() {
  return state.events.filter((event) => {
    return (!state.city || event.city === state.city) && (!state.genre || event.genre === state.genre);
  });
}

function renderFilters() {
  const cities = [...new Set(state.events.map((event) => event.city))].sort();
  const genres = [...new Set(state.events.map((event) => event.genre))].sort();
  els.cityFilter.innerHTML = `<option value="">All cities</option>${cities.map((city) => `<option>${city}</option>`).join("")}`;
  els.genreFilter.innerHTML = `<option value="">All genres</option>${genres.map((genre) => `<option>${genre}</option>`).join("")}`;
}

function renderEvents() {
  const events = filteredEvents();
  els.eventList.innerHTML = "";
  events.forEach((event) => {
    const selected = event.id === state.selectedEventId;
    const card = document.createElement("article");
    card.className = `event-card${selected ? " is-selected" : ""}`;
    card.innerHTML = `
      <div class="${eventPosterClass(event)}" aria-hidden="true">
        <span>${event.genre}</span>
        <strong>${event.artist.split(" ").map((part) => part[0]).join("")}</strong>
      </div>
      <div class="event-copy">
        <div class="event-meta">
          <span>${event.city}</span>
          <span>${event.date}</span>
        </div>
        <h2>${event.artist}</h2>
        <p>${event.summary}</p>
        <div class="event-footer">
          <span>${event.venue}</span>
          <strong>from ${money(event.lowest_total_per_ticket)}</strong>
        </div>
      </div>
    `;
    card.addEventListener("click", () => {
      state.selectedEventId = event.id;
      renderEvents();
      els.chatInput.value = `Help me plan ${els.ticketCount.value} tickets for ${event.artist} within a ${money(Number(els.budgetInput.value))} budget.`;
      els.chatInput.focus();
    });
    els.eventList.append(card);
  });
}

function appendMessage(role, text, meta = "") {
  const node = document.createElement("div");
  node.className = `message ${role}`;
  const metaNode = document.createElement("div");
  metaNode.className = "message-meta";
  metaNode.textContent = meta || (role === "user" ? "You" : "TicketMate");
  const bodyNode = document.createElement("div");
  bodyNode.className = "message-body";
  bodyNode.textContent = text;
  node.append(metaNode, bodyNode);
  els.chatLog.append(node);
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
}

function renderAgents(agents = []) {
  if (!agents.length) {
    els.agentTimeline.innerHTML = `<div class="empty-state">No agent activity returned.</div>`;
    return;
  }
  els.agentTimeline.innerHTML = agents
    .map(
      (agent, index) => `
        <article class="agent-step">
          <div class="agent-index">${index + 1}</div>
          <div>
            <h3>${agent.name}</h3>
            <p>${agent.output || ""}</p>
            <span>${agent.usage?.total_tokens || 0} tokens</span>
          </div>
        </article>
      `,
    )
    .join("");
}

function updateUsage(usage = {}, latencyMs = 0) {
  const total = Number(usage.total_tokens || 0);
  state.sessionTokens += total;
  els.sessionTokens.textContent = String(state.sessionTokens);
  els.lastTokens.textContent = String(total);
  els.lastLatency.textContent = `${latencyMs || 0} ms`;
}

async function loadHealth() {
  try {
    const response = await fetch("/healthz");
    const health = await response.json();
    els.modelName.textContent = health.model || "model unknown";
    if (health.nim_reachable) {
      els.nimStatus.textContent = "NIM reachable";
      els.nimStatus.classList.add("is-live");
    } else if (health.nim_configured) {
      els.nimStatus.textContent = "NIM configured";
      els.nimStatus.classList.remove("is-live");
    } else {
      els.nimStatus.textContent = "NIM missing";
      els.nimStatus.classList.remove("is-live");
    }
  } catch {
    els.modelName.textContent = "model unknown";
    els.nimStatus.textContent = "offline";
  }
}

async function loadEvents() {
  const response = await fetch("/api/events");
  const data = await response.json();
  state.events = data.events || [];
  state.selectedEventId = state.events[0]?.id || "";
  renderFilters();
  renderEvents();
}

async function sendMessage(message) {
  const trimmed = message.trim();
  if (!trimmed) return;

  appendMessage("user", trimmed);
  state.history.push({ role: "user", content: trimmed });
  els.chatInput.value = "";
  els.chatForm.querySelector("button").disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: trimmed,
        history: state.history.slice(-8),
        event_id: state.selectedEventId,
        tickets: Number(els.ticketCount.value || 2),
        budget: Number(els.budgetInput.value || 0),
        city: state.city,
        genre: state.genre,
        scenario: els.scenarioSelect.value,
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "TicketMate request failed");
    appendMessage("assistant", data.reply, `${data.model} / ${data.usage.total_tokens} tokens`);
    state.history.push({ role: "assistant", content: data.reply });
    updateUsage(data.usage, data.latency_ms);
    renderAgents(data.agents);
  } catch (error) {
    appendMessage("assistant", error.message, "Model error");
    renderAgents([]);
  } finally {
    els.chatForm.querySelector("button").disabled = false;
    els.chatInput.focus();
  }
}

function bindEvents() {
  els.cityFilter.addEventListener("change", () => {
    state.city = els.cityFilter.value;
    renderEvents();
  });
  els.genreFilter.addEventListener("change", () => {
    state.genre = els.genreFilter.value;
    renderEvents();
  });
  els.chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage(els.chatInput.value);
  });
  els.chatInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage(els.chatInput.value);
    }
  });
}

async function boot() {
  bindEvents();
  appendMessage("assistant", "Choose an event or ask me to plan a concert night for your group.", "TicketMate");
  await Promise.all([loadHealth(), loadEvents()]);
}

boot();

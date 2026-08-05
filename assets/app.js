/* TATTS — thư viện nghe thử giọng đọc AI. Toàn bộ dữ liệu nạp từ data/voices.json */
(() => {
  "use strict";

  const DATA_URL = "data/voices.json";
  const SPEEDS = [0.75, 1, 1.25, 1.5];
  const ICON_PLAY = "▶";
  const ICON_PAUSE = "❚❚";

  const el = {
    grid: document.getElementById("grid"),
    empty: document.getElementById("empty"),
    facets: document.getElementById("facets"),
    search: document.getElementById("search"),
    sort: document.getElementById("sort"),
    resultCount: document.getElementById("result-count"),
    resetFilters: document.getElementById("reset-filters"),
    sidebar: document.getElementById("sidebar"),
    menuToggle: document.getElementById("menu-toggle"),
    player: document.getElementById("player"),
    playerName: document.getElementById("player-name"),
    playerMeta: document.getElementById("player-meta"),
    audio: document.getElementById("audio"),
    toggle: document.getElementById("toggle"),
    prev: document.getElementById("prev"),
    next: document.getElementById("next"),
    seek: document.getElementById("seek"),
    timeNow: document.getElementById("time-now"),
    timeTotal: document.getElementById("time-total"),
    speed: document.getElementById("speed"),
    volume: document.getElementById("volume"),
    closePlayer: document.getElementById("close-player"),
  };

  const state = {
    voices: [],
    visible: [],
    filters: { query: "", language: null },
    sort: "name",
    currentId: null,
    speedIndex: 1,
    isSeeking: false,
  };

  /* ---------- tiện ích ---------- */

  const normalize = (text) =>
    text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[đĐ]/g, "d").toLowerCase();

  const formatTime = (seconds) => {
    if (!Number.isFinite(seconds)) return "0:00";
    const total = Math.floor(seconds);
    return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
  };

  const findVoice = (id) => state.voices.find((voice) => voice.id === id) || null;

  /** Chặn HTML lạ trong tên giọng / kịch bản trước khi chèn vào DOM. */
  const escapeHtml = (text) =>
    String(text).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[char]));

  /* ---------- lọc & sắp xếp ---------- */

  function applyFilters() {
    const { query, language } = state.filters;
    const needle = normalize(query.trim());

    state.visible = state.voices.filter((voice) => {
      if (language && voice.language !== language) return false;
      if (needle && !normalize(voice.name).includes(needle)) return false;
      return true;
    });

    const sorters = {
      name: (a, b) => a.name.localeCompare(b.name, "vi"),
      "duration-desc": (a, b) => b.duration - a.duration,
      "duration-asc": (a, b) => a.duration - b.duration,
    };
    state.visible.sort(sorters[state.sort]);
  }

  /* ---------- menu bộ lọc ---------- */

  function countBy(key) {
    const counts = new Map();
    state.voices.forEach((voice) => {
      counts.set(voice[key], (counts.get(voice[key]) || 0) + 1);
    });
    return counts;
  }

  function buildFacet(title, key, entries) {
    const section = document.createElement("section");
    section.className = "facet";
    section.innerHTML = `<h2>${title}</h2>`;

    const makeButton = (value, label, count) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "facet-item";
      button.setAttribute("aria-pressed", String(state.filters[key] === value));
      button.innerHTML = `<span>${escapeHtml(label)}</span><span class="count">${count}</span>`;
      button.addEventListener("click", () => {
        state.filters[key] = state.filters[key] === value ? null : value;
        renderFacets();
        renderGrid();
      });
      return button;
    };

    section.appendChild(makeButton(null, "Tất cả", state.voices.length));
    entries.forEach(([value, count]) => {
      section.appendChild(makeButton(value, value, count));
    });
    return section;
  }

  function sortedCounts(key) {
    return [...countBy(key)].sort((a, b) => String(a[0]).localeCompare(String(b[0]), "vi"));
  }

  function renderFacets() {
    el.facets.replaceChildren(buildFacet("Ngôn ngữ", "language", sortedCounts("language")));
  }

  /* ---------- danh sách giọng ---------- */

  function createCard(voice) {
    const isActive = voice.id === state.currentId;
    const card = document.createElement("article");
    card.className = `card${isActive ? " is-active" : ""}`;
    card.dataset.id = voice.id;

    const scriptId = `script-${voice.id}`;
    const isPlaying = isActive && !el.audio.paused;
    const name = escapeHtml(voice.name);

    card.innerHTML = `
      <div class="card-top">
        <button class="card-play" type="button" aria-label="Nghe thử ${name}">${isPlaying ? ICON_PAUSE : ICON_PLAY}</button>
        <div class="card-title">
          <h3>${name}</h3>
          <div class="sub">${escapeHtml(voice.language)} · ${formatTime(voice.duration)}</div>
        </div>
      </div>
      ${voice.script ? `<button class="script-toggle" type="button" aria-expanded="false" aria-controls="${scriptId}">Xem kịch bản demo</button>
      <p class="script" id="${scriptId}" hidden>${escapeHtml(voice.script)}</p>` : ""}
    `;

    card.querySelector(".card-play").addEventListener("click", () => playVoice(voice.id));

    const scriptToggle = card.querySelector(".script-toggle");
    if (scriptToggle) {
      scriptToggle.addEventListener("click", () => {
        const script = card.querySelector(".script");
        const willShow = script.hidden;
        script.hidden = !willShow;
        scriptToggle.setAttribute("aria-expanded", String(willShow));
        scriptToggle.textContent = willShow ? "Ẩn kịch bản" : "Xem kịch bản demo";
      });
    }
    return card;
  }

  function renderGrid() {
    applyFilters();
    el.grid.replaceChildren(...state.visible.map(createCard));
    el.empty.hidden = state.visible.length > 0;
    el.resultCount.textContent = `${state.visible.length} giọng${
      state.visible.length !== state.voices.length ? ` / ${state.voices.length}` : ""
    }`;
  }

  function refreshPlayButtons() {
    const isPlaying = !el.audio.paused;
    el.toggle.textContent = isPlaying ? ICON_PAUSE : ICON_PLAY;
    el.grid.querySelectorAll(".card").forEach((card) => {
      const isActive = card.dataset.id === state.currentId;
      card.classList.toggle("is-active", isActive);
      card.querySelector(".card-play").textContent = isActive && isPlaying ? ICON_PAUSE : ICON_PLAY;
    });
  }

  /* ---------- trình phát ---------- */

  function playVoice(id) {
    if (id === state.currentId) {
      if (el.audio.paused) el.audio.play(); else el.audio.pause();
      return;
    }

    const voice = findVoice(id);
    if (!voice) return;

    state.currentId = id;
    el.audio.src = voice.audio;
    el.audio.play().catch(() => {});

    el.player.hidden = false;
    el.playerName.textContent = voice.name;
    el.playerMeta.textContent = voice.language;
    el.timeTotal.textContent = formatTime(voice.duration);
    history.replaceState(null, "", `#${id}`);
    refreshPlayButtons();
  }

  function step(offset) {
    if (!state.visible.length) return;
    const index = state.visible.findIndex((voice) => voice.id === state.currentId);
    const nextIndex = (index + offset + state.visible.length) % state.visible.length;
    playVoice(state.visible[nextIndex].id);
  }

  function bindPlayer() {
    el.toggle.addEventListener("click", () => {
      if (el.audio.paused) el.audio.play(); else el.audio.pause();
    });
    el.prev.addEventListener("click", () => step(-1));
    el.next.addEventListener("click", () => step(1));
    el.audio.addEventListener("play", refreshPlayButtons);
    el.audio.addEventListener("pause", refreshPlayButtons);
    el.audio.addEventListener("ended", () => step(1));

    el.audio.addEventListener("loadedmetadata", () => {
      el.timeTotal.textContent = formatTime(el.audio.duration);
    });

    el.audio.addEventListener("timeupdate", () => {
      if (state.isSeeking || !Number.isFinite(el.audio.duration)) return;
      el.seek.value = String((el.audio.currentTime / el.audio.duration) * 100);
      el.timeNow.textContent = formatTime(el.audio.currentTime);
    });

    el.seek.addEventListener("input", () => {
      state.isSeeking = true;
      if (Number.isFinite(el.audio.duration)) {
        el.timeNow.textContent = formatTime((Number(el.seek.value) / 100) * el.audio.duration);
      }
    });

    el.seek.addEventListener("change", () => {
      if (Number.isFinite(el.audio.duration)) {
        el.audio.currentTime = (Number(el.seek.value) / 100) * el.audio.duration;
      }
      state.isSeeking = false;
    });

    el.volume.addEventListener("input", () => {
      el.audio.volume = Number(el.volume.value);
    });

    el.speed.addEventListener("click", () => {
      state.speedIndex = (state.speedIndex + 1) % SPEEDS.length;
      el.audio.playbackRate = SPEEDS[state.speedIndex];
      el.speed.textContent = `${SPEEDS[state.speedIndex]}×`;
    });

    el.closePlayer.addEventListener("click", () => {
      el.audio.pause();
      el.player.hidden = true;
      state.currentId = null;
      history.replaceState(null, "", location.pathname);
      refreshPlayButtons();
    });
  }

  /* ---------- điều khiển chung ---------- */

  function bindControls() {
    let searchTimer;
    el.search.addEventListener("input", () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        state.filters.query = el.search.value;
        renderGrid();
      }, 120);
    });

    el.sort.addEventListener("change", () => {
      state.sort = el.sort.value;
      renderGrid();
    });

    el.resetFilters.addEventListener("click", () => {
      state.filters = { query: "", language: null };
      el.search.value = "";
      renderFacets();
      renderGrid();
    });

    el.menuToggle.addEventListener("click", () => {
      const isOpen = el.sidebar.classList.toggle("is-open");
      el.menuToggle.setAttribute("aria-expanded", String(isOpen));
    });

    document.addEventListener("keydown", (event) => {
      const inField = /^(INPUT|TEXTAREA|SELECT)$/.test(event.target.tagName);
      if (event.key === "/" && !inField) {
        event.preventDefault();
        el.search.focus();
      } else if (event.key === " " && !inField && state.currentId) {
        event.preventDefault();
        el.toggle.click();
      } else if (event.key === "Escape" && inField) {
        el.search.blur();
      }
    });
  }

  /* ---------- khởi động ---------- */

  async function init() {
    bindPlayer();
    bindControls();

    try {
      const response = await fetch(DATA_URL);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      state.voices = (await response.json()).voices || [];
    } catch (error) {
      el.empty.hidden = false;
      el.empty.textContent = `Không tải được danh sách giọng (${error.message}). Hãy mở trang qua máy chủ web, không mở trực tiếp file.`;
      return;
    }

    renderFacets();
    renderGrid();

    const shared = decodeURIComponent(location.hash.slice(1));
    if (shared && findVoice(shared)) playVoice(shared);
  }

  init();
})();

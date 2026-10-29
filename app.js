// app.js - Mobile-First Japan PWA Engine
let itineraryData = null;
let currentDayIndex = 1;
let currentFilter = 'all';
let currentTab = 'itinerary'; // 'itinerary' | 'checklist' | 'sync' | 'guide'
let completedItems = JSON.parse(localStorage.getItem('japan_trip_completed') || '{}');
let customCalendarEvents = JSON.parse(localStorage.getItem('japan_trip_calendar_events') || '[]');

// Packing / Trip Checklist Storage
const DEFAULT_CHECKLIST_ITEMS = [
  { id: 'chk-1', text: 'Passport & International Driving Permit (if needed)', completed: true, category: 'Docs' },
  { id: 'chk-2', text: 'Visit Japan Web QR codes (Customs & Immigration)', completed: true, category: 'Docs' },
  { id: 'chk-3', text: 'Load digital Suica / Pasmo in Apple Wallet', completed: true, category: 'Transit' },
  { id: 'chk-4', text: 'eSIM / Pocket WiFi activation & confirmation', completed: true, category: 'Gear' },
  { id: 'chk-5', text: 'Shinkansen & Thunderbird train reservations', completed: false, category: 'Transit' },
  { id: 'chk-6', text: 'Universal travel plug adapter (Japan uses Type A)', completed: false, category: 'Gear' },
  { id: 'chk-7', text: 'Portable power bank (10,000+ mAh) for all-day maps', completed: false, category: 'Gear' },
  { id: 'chk-8', text: 'Japanese Yen Cash (¥15,000-¥30,000 for shrines & street food)', completed: false, category: 'Money' },
  { id: 'chk-9', text: 'Credit card with 0% foreign transaction fees (Wise / Revolut)', completed: true, category: 'Money' },
  { id: 'chk-10', text: 'Comfortable slip-on walking shoes (easy for temple entry)', completed: false, category: 'Packing' },
  { id: 'chk-11', text: 'Coin pouch (Japan generates lots of 100 & 500 yen coins)', completed: false, category: 'Packing' },
  { id: 'chk-12', text: 'Luggage lock & forward address (Takkyubin service)', completed: false, category: 'Packing' }
];

let checklistItems = JSON.parse(localStorage.getItem('japan_trip_checklist') || 'null');
if (!checklistItems || !Array.isArray(checklistItems) || checklistItems.length === 0) {
  checklistItems = DEFAULT_CHECKLIST_ITEMS;
  localStorage.setItem('japan_trip_checklist', JSON.stringify(checklistItems));
}

// Per-card collapse state memory: key is item.id, value is boolean (true = collapsed)
let cardCollapseState = {};
let allCollapsed = false;

// DOM Elements
const daysNavEl = document.getElementById('days-nav');
const dayContentEl = document.getElementById('day-content');
const checklistViewEl = document.getElementById('checklist-view');
const filterBarEl = document.querySelector('.filter-bar');
const daysNavContainerEl = document.querySelector('.days-nav-container');
const calModalEl = document.getElementById('calendar-modal');
const handbookModalEl = document.getElementById('handbook-modal');
const syncStatusBtnEl = document.getElementById('sync-status-btn');

// Initialize App
async function initApp() {
  registerServiceWorker();
  await loadItineraryData();
  renderDaysNav();
  renderCurrentDay();
  renderChecklistView();
  updateSyncButtonState();
  setupEventListeners();
}

// 1. Data Loader with Offline Fallback
async function loadItineraryData() {
  const localCache = localStorage.getItem('japan_master_itinerary');
  if (localCache) {
    try {
      itineraryData = JSON.parse(localCache);
    } catch (e) {
      console.warn('Failed parsing local storage itinerary cache', e);
    }
  }

  try {
    const res = await fetch('./master_itinerary.json');
    if (res.ok) {
      itineraryData = await res.json();
      localStorage.setItem('japan_master_itinerary', JSON.stringify(itineraryData));
    }
  } catch (err) {
    console.log('[Offline] Using cached master itinerary', err);
  }

  if (!itineraryData) {
    dayContentEl.innerHTML = `
      <div style="padding: 24px; text-align: center; color: #94a3b8;">
        <h3>No Offline Itinerary Found</h3>
        <p>Please connect to the internet once to cache your trip data.</p>
      </div>`;
  }
}

// 2. Render Horizontal Day Pill Bar
function renderDaysNav() {
  if (!itineraryData || !itineraryData.days) return;

  daysNavEl.innerHTML = itineraryData.days.map((day) => {
    const isActive = day.day_index === currentDayIndex;
    const dateParts = day.display_date.split(', ');
    const shortDate = dateParts[1] || `D${day.day_index}`;
    return `
      <div class="day-pill ${isActive ? 'active' : ''}" data-day="${day.day_index}">
        <span class="dp-day">D${day.day_index}</span>
        <span class="dp-date">${shortDate}</span>
        <span class="dp-city">${escapeHtml(day.city)}</span>
      </div>
    `;
  }).join('');

  // Scroll active pill into view smoothly
  const activePill = daysNavEl.querySelector('.day-pill.active');
  if (activePill) {
    activePill.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
  }
}

// 3. Calendar Event Deduplication & Merging Helpers
function normalizeTitle(str) {
  return String(str || '')
    .replace(/[\u{1F300}-\u{1FFFF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '')
    .replace(/[✈️🚄🚆🚞🚌🚃🚋🛫🛬]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

function itemsOverlapByKeywords(titleA, titleB) {
  const a = normalizeTitle(titleA);
  const b = normalizeTitle(titleB);
  if (!a || !b) return false;
  if (a === b) return true;

  // Transit & Flight key destination matches
  const keyTransitRoots = ['osaka', 'shin-osaka', 'shinkansen', 'flight', 'haneda', 'tokyo', 'koya', 'kanazawa', 'takayama', 'shirakawa', 'kyoto'];
  for (const root of keyTransitRoots) {
    const rootMatchesA = a.includes(root);
    const rootMatchesB = b.includes(root);
    if (rootMatchesA && rootMatchesB) {
      const isTransitA = /train|shinkansen|flight|express|bus/.test(a);
      const isTransitB = /train|shinkansen|flight|express|bus/.test(b);
      if (isTransitA && isTransitB) return true;
    }
  }

  // General keyword intersection (words of 3+ characters)
  const wordsA = a.split(/\s+/).filter(w => w.length >= 3);
  const wordsB = new Set(b.split(/\s+/).filter(w => w.length >= 3));
  const shared = wordsA.filter(w => wordsB.has(w));
  return shared.length >= 2;
}

function mergeCalendarEventIntoItem(item, cal) {
  if (!item || !cal) return;

  if (!item.scheduled_time && cal.time) {
    item.scheduled_time = cal.time;
  }
  if (!item.address && cal.location) {
    item.address = cal.location;
  }
  if (cal.location && !item.google_maps_url) {
    item.google_maps_url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(cal.location)}`;
  }
  if (cal.description && (!item.user_notes || cal.description.length > item.user_notes.length)) {
    item.user_notes = cal.description;
  }
  if (cal.category && !item.category) {
    item.category = cal.category;
  }

  item.is_calendar_event = true;
  item.calendar_event = {
    synced: true,
    event_id: cal.id || (item.calendar_event && item.calendar_event.event_id) || null,
    summary: item.title,
    time_start: item.scheduled_time || cal.time || (item.calendar_event && item.calendar_event.time_start) || null,
    time_end: cal.time_end || null
  };
}

function itemSortKey(item) {
  const timeStr = item.scheduled_time || (item.calendar_event && item.calendar_event.time_start) || '';
  const match = timeStr.match(/^(\d{1,2}):(\d{2})/);
  if (match) {
    return parseInt(match[1], 10) * 60 + parseInt(match[2], 10);
  }
  return 99999;
}

// 4. Render Current Selected Day
function renderCurrentDay() {
  if (!itineraryData) return;

  const day = itineraryData.days.find(d => d.day_index === currentDayIndex);
  if (!day) return;

  const dayDate = day.date;
  const mergedItems = [...(day.items || [])].map(item => ({ ...item }));

  // Add synced calendar events — deduplicate and merge into itinerary item
  const matchedCalEvents = customCalendarEvents.filter(ev => ev.date === dayDate);
  matchedCalEvents.forEach(cal => {
    const existingIndex = mergedItems.findIndex(it => itemsOverlapByKeywords(it.title, cal.title));
    if (existingIndex >= 0) {
      const match = mergedItems[existingIndex];
      mergeCalendarEventIntoItem(match, cal);
      return;
    }

    mergedItems.unshift({
      id: `cal-${cal.id || Math.random().toString(36).substr(2, 9)}`,
      title: cal.title,
      category: cal.category || 'transport',
      order: 0,
      city: day.city,
      cost_eur: null,
      cost_jpy: null,
      address: cal.location || null,
      google_maps_url: cal.location ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(cal.location)}` : null,
      scheduled_time: cal.time || null,
      pacing_note: null,
      opening_hours: null,
      user_notes: cal.description || 'Synced from Google Calendar',
      is_calendar_event: true,
      calendar_event: { synced: true, event_id: cal.id || null, time_start: cal.time || null }
    });
  });

  // Sort chronologically
  mergedItems.sort((a, b) => itemSortKey(a) - itemSortKey(b));

  // Filter items
  const filteredItems = mergedItems.filter(item => {
    if (currentFilter === 'all') return true;
    if (currentFilter === 'attraction') return item.category === 'attraction';
    if (currentFilter === 'restaurant') return item.category === 'restaurant' || item.category === 'cafe';
    if (currentFilter === 'transport') return item.category === 'transport' || item.category === 'flight';
    if (currentFilter === 'shopping') return item.category === 'shopping';
    return true;
  });

  // Hotel card
  const hotelHtml = day.accommodation ? `
    <div class="hotel-card">
      <div class="hotel-icon">🏨</div>
      <div class="hotel-details">
        <div class="hotel-label">Tonight's Stay</div>
        <div class="hotel-name">${escapeHtml(day.accommodation.name)}</div>
        ${day.accommodation.address ? `<div class="hotel-address">${escapeHtml(day.accommodation.address)}</div>` : ''}
        <div class="hotel-actions">
          ${day.accommodation.maps_url ? `<a href="${day.accommodation.maps_url}" target="_blank" rel="noopener" class="btn-mini btn-mini-primary">🗺️ Navigate</a>` : ''}
          ${day.accommodation.website ? `<a href="${day.accommodation.website}" target="_blank" rel="noopener" class="btn-mini btn-mini-secondary">🌐 Booking Details</a>` : ''}
        </div>
      </div>
    </div>
  ` : '';

  // Tailored Recommendations — rendered strictly AFTER day schedule
  const recs = day.tailored_recommendations;
  let recsHtml = '';
  if (recs && recs.highlights && recs.highlights.length > 0) {
    const recList = recs.highlights.map(h => `
      <div class="rec-item">
        <div class="rec-item-title">
          <span>${escapeHtml(h.title)}</span>
          <span class="rec-item-cat">${escapeHtml(h.category)}</span>
        </div>
        <div class="rec-item-desc">${escapeHtml(h.description)}</div>
        <a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(h.maps_query || h.title)}" target="_blank" rel="noopener" class="btn-mini btn-mini-secondary">
          🗺️ Find Nearby in Maps
        </a>
      </div>
    `).join('');

    recsHtml = `
      <div class="recommendations-card" style="margin-top: 24px;">
        <div class="rec-header">
          <div class="rec-title-group">
            <span class="rec-badge">Curated Gems</span>
            <div class="rec-title">Tailored for ${escapeHtml(recs.neighborhood || day.city)}</div>
          </div>
          <span style="font-size: 0.8rem; color: #818cf8;">✨ Autumn Tips</span>
        </div>
        <div class="rec-items-list">
          ${recList}
        </div>
      </div>
    `;
  }

  // Items List HTML — collapsible with clean, uncluttered UX
  const itemsHtml = filteredItems.length > 0 ? filteredItems.map(item => {
    const isDone = !!completedItems[item.id];
    const catClass = `cat-${item.category || 'other'}`;
    const isCollapsed = cardCollapseState[item.id] !== undefined ? cardCollapseState[item.id] : allCollapsed;

    const expandedBody = `
      <div class="card-body">
        <div class="card-meta-list">
          ${item.opening_hours ? `
            <div class="meta-row">
              <span class="meta-icon">⏰</span>
              <span><strong>Hours:</strong> ${escapeHtml(item.opening_hours)}</span>
            </div>
          ` : ''}
          ${item.address ? `
            <div class="meta-row">
              <span class="meta-icon">📍</span>
              <span style="font-size: 0.78rem;">${escapeHtml(item.address)}</span>
            </div>
          ` : ''}
          ${item.user_notes ? `
            <div class="meta-row" style="color: #fde68a;">
              <span class="meta-icon">📝</span>
              <span>${escapeHtml(item.user_notes)}</span>
            </div>
          ` : ''}
        </div>

        ${item.how_to_access ? `
          <div class="access-box">
            <strong>🚶 Getting There:</strong> ${escapeHtml(item.how_to_access)}
          </div>
        ` : ''}

        ${item.highlights && item.highlights.length > 0 ? `
          <div class="highlights-box">
            <div class="highlights-title">⭐ Guidebook Highlights:</div>
            <ul>
              ${item.highlights.map(hl => `<li>${escapeHtml(hl)}</li>`).join('')}
            </ul>
          </div>
        ` : ''}

        ${item.travel_tip ? `
          <div class="tip-callout">
            💡 <strong>Tip:</strong> ${escapeHtml(item.travel_tip)}
          </div>
        ` : ''}

        <div class="card-actions-toolbar">
          ${item.google_maps_url ? `
            <a href="${item.google_maps_url}" target="_blank" rel="noopener" class="btn-action btn-action-maps">
              🗺️ Open in Google Maps
            </a>
          ` : `
            <a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(item.title + ' ' + (item.city || 'Japan'))}" target="_blank" rel="noopener" class="btn-action btn-action-maps">
              🗺️ Search on Maps
            </a>
          `}
          ${item.website ? `
            <a href="${item.website}" target="_blank" rel="noopener" class="btn-action btn-action-web">
              🌐 Official Website
            </a>
          ` : ''}
        </div>
      </div>
    `;

    return `
      <div class="itinerary-card ${isDone ? 'completed' : ''} ${isCollapsed ? 'card-collapsed' : ''}" id="card-${item.id}">
        <div class="card-header-row" data-card-id="${item.id}">
          <div class="card-header-left">
            <div class="card-badges">
              ${item.scheduled_time ? `<span class="time-badge">⏰ ${escapeHtml(item.scheduled_time)}</span>` : ''}
              <span class="category-badge ${catClass}">${item.category || 'Activity'}</span>
              ${item.is_calendar_event ? `<span class="category-badge" style="background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid #10b981;">📅 G-Cal</span>` : ''}
            </div>
            <div class="card-title">${escapeHtml(item.title)}</div>
            ${item.pacing_note && !isCollapsed ? `<div class="pacing-tag">⏳ ${escapeHtml(item.pacing_note)}</div>` : ''}
            ${item.tagline && !isCollapsed ? `<div class="card-tagline">"${escapeHtml(item.tagline)}"</div>` : ''}
          </div>
          <div class="card-header-actions">
            <button class="check-btn ${isDone ? 'checked' : ''}" data-id="${item.id}" title="Mark completed">
              ${isDone ? '✓' : ''}
            </button>
            <button class="collapse-btn" data-card-id="${item.id}" title="${isCollapsed ? 'Expand' : 'Collapse'}">
              ${isCollapsed ? '›' : '‹'}
            </button>
          </div>
        </div>
        ${isCollapsed ? '' : expandedBody}
      </div>
    `;
  }).join('') : `
    <div style="padding: 24px; text-align: center; color: #94a3b8; background: var(--bg-surface); border-radius: var(--radius-md); border: 1px dashed var(--border-subtle);">
      No items match the selected category.
    </div>
  `;

  // Render Day container — schedule first, Curated Gems at bottom
  dayContentEl.innerHTML = `
    <div class="day-header-card">
      <div class="day-meta-row">
        <span class="day-tag">Day ${day.day_index} of ${itineraryData.metadata.total_days}</span>
        <span class="city-badge">📍 ${day.city}</span>
      </div>
      <h2 class="day-title">${escapeHtml(day.title)}</h2>
      <div class="day-date-display">🗓️ ${escapeHtml(day.display_date)}, 2026</div>
      ${hotelHtml}
    </div>

    <div class="section-title-row">
      <h3 class="section-title">Day Schedule (${filteredItems.length} items)</h3>
      <button id="toggle-collapse-btn" class="collapse-all-btn" title="${allCollapsed ? 'Expand all cards' : 'Collapse all cards'}">
        ${allCollapsed ? '⊞ Expand All' : '⊟ Collapse All'}
      </button>
    </div>

    <div class="timeline-list">
      ${itemsHtml}
    </div>

    ${recsHtml}
  `;

  // Bind collapse-all toggle
  document.getElementById('toggle-collapse-btn').addEventListener('click', () => {
    allCollapsed = !allCollapsed;
    cardCollapseState = {};
    renderCurrentDay();
  });

  // Bind per-card collapse buttons
  dayContentEl.querySelectorAll('.collapse-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = btn.dataset.cardId;
      const current = cardCollapseState[id] !== undefined ? cardCollapseState[id] : allCollapsed;
      cardCollapseState[id] = !current;
      renderCurrentDay();
    });
  });

  // Make header row clickable for easy expanding/collapsing on mobile
  dayContentEl.querySelectorAll('.card-header-left').forEach(leftEl => {
    leftEl.addEventListener('click', () => {
      const parentRow = leftEl.closest('.card-header-row');
      const id = parentRow.dataset.cardId;
      const current = cardCollapseState[id] !== undefined ? cardCollapseState[id] : allCollapsed;
      cardCollapseState[id] = !current;
      renderCurrentDay();
    });
  });
}

// 5. Checklist Feature Implementation
function renderChecklistView() {
  if (!checklistViewEl) return;

  const total = checklistItems.length;
  const completedCount = checklistItems.filter(i => i.completed).length;
  const progressPercent = total > 0 ? Math.round((completedCount / total) * 100) : 0;

  const itemsHtml = checklistItems.map((item, idx) => `
    <div class="checklist-item ${item.completed ? 'checked' : ''}" data-index="${idx}">
      <button class="checklist-checkbox" data-index="${idx}">
        ${item.completed ? '✓' : ''}
      </button>
      <div class="checklist-text-wrap">
        <span class="checklist-text">${escapeHtml(item.text)}</span>
        ${item.category ? `<span class="checklist-cat-badge">${escapeHtml(item.category)}</span>` : ''}
      </div>
      <button class="checklist-del-btn" data-index="${idx}" title="Remove item">×</button>
    </div>
  `).join('');

  checklistViewEl.innerHTML = `
    <div class="checklist-header-card">
      <div class="checklist-title-row">
        <div>
          <h2 class="checklist-title">📋 Trip Essentials & Packing Checklist</h2>
          <p class="checklist-subtitle">Don't forget the vital items before taking off to Japan.</p>
        </div>
        <span class="checklist-counter">${completedCount}/${total} Done</span>
      </div>

      <div class="checklist-progress-bar">
        <div class="checklist-progress-fill" style="width: ${progressPercent}%;"></div>
      </div>
    </div>

    <!-- Add Item Input Form -->
    <form id="checklist-add-form" class="checklist-add-bar">
      <input type="text" id="checklist-input" class="checklist-input" placeholder="Add an item not to forget..." required autocomplete="off" />
      <button type="submit" class="checklist-add-btn">+ Add</button>
    </form>

    <!-- Checklist Items List -->
    <div class="checklist-items-list">
      ${itemsHtml}
    </div>

    <div style="margin-top: 20px; display: flex; justify-content: space-between; align-items: center;">
      <button id="btn-reset-checklist" class="btn-mini btn-mini-secondary" style="color: #94a3b8; font-size: 0.76rem;">
        ↺ Reset Default Travel Items
      </button>
      <button id="btn-clear-done-checklist" class="btn-mini btn-mini-secondary" style="color: #f87171; font-size: 0.76rem;">
        🗑️ Clear Completed
      </button>
    </div>
  `;

  // Bind Form Submit
  const addForm = document.getElementById('checklist-add-form');
  addForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const inputEl = document.getElementById('checklist-input');
    const text = inputEl.value.trim();
    if (text) {
      checklistItems.unshift({
        id: `chk-${Date.now()}`,
        text: text,
        completed: false,
        category: 'Personal'
      });
      saveChecklist();
      renderChecklistView();
    }
  });

  // Bind Checkbox Toggle
  checklistViewEl.querySelectorAll('.checklist-checkbox, .checklist-text-wrap').forEach(el => {
    el.addEventListener('click', (e) => {
      const idx = parseInt(el.dataset.index || el.closest('.checklist-item').dataset.index, 10);
      checklistItems[idx].completed = !checklistItems[idx].completed;
      saveChecklist();
      renderChecklistView();
    });
  });

  // Bind Delete Item
  checklistViewEl.querySelectorAll('.checklist-del-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const idx = parseInt(btn.dataset.index, 10);
      checklistItems.splice(idx, 1);
      saveChecklist();
      renderChecklistView();
    });
  });

  // Bind Reset & Clear
  document.getElementById('btn-reset-checklist').addEventListener('click', () => {
    if (confirm('Reset to standard Japan packing checklist?')) {
      checklistItems = [...DEFAULT_CHECKLIST_ITEMS];
      saveChecklist();
      renderChecklistView();
    }
  });

  document.getElementById('btn-clear-done-checklist').addEventListener('click', () => {
    checklistItems = checklistItems.filter(i => !i.completed);
    saveChecklist();
    renderChecklistView();
  });
}

function saveChecklist() {
  localStorage.setItem('japan_trip_checklist', JSON.stringify(checklistItems));
}

// 6. Tab Switching Engine
function switchTab(tabName) {
  currentTab = tabName;
  document.querySelectorAll('.nav-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === tabName);
  });

  if (tabName === 'itinerary') {
    dayContentEl.style.display = 'block';
    checklistViewEl.style.display = 'none';
    if (filterBarEl) filterBarEl.style.display = 'flex';
    if (daysNavContainerEl) daysNavContainerEl.style.display = 'block';
    closeModals();
    renderCurrentDay();
  } else if (tabName === 'checklist') {
    dayContentEl.style.display = 'none';
    checklistViewEl.style.display = 'block';
    if (filterBarEl) filterBarEl.style.display = 'none';
    if (daysNavContainerEl) daysNavContainerEl.style.display = 'none';
    closeModals();
    renderChecklistView();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } else if (tabName === 'sync') {
    calModalEl.classList.add('open');
  } else if (tabName === 'guide') {
    populateHandbookModal();
    handbookModalEl.classList.add('open');
  }
}

// 7. Calendar Sync Handlers
function updateSyncButtonState() {
  if (customCalendarEvents.length > 0) {
    syncStatusBtnEl.classList.add('synced');
    syncStatusBtnEl.innerHTML = `📅 Synced (${customCalendarEvents.length})`;
  } else {
    syncStatusBtnEl.classList.remove('synced');
    syncStatusBtnEl.innerHTML = `📅 Sync Calendar`;
  }
}

function parseIcsFeed(icsText) {
  const events = [];
  const lines = icsText.split(/\r\n|\n|\r/);
  let currentEvent = null;

  for (let line of lines) {
    if (line.startsWith('BEGIN:VEVENT')) {
      currentEvent = {};
    } else if (line.startsWith('END:VEVENT')) {
      if (currentEvent && currentEvent.title && currentEvent.date) {
        events.push(currentEvent);
      }
      currentEvent = null;
    } else if (currentEvent) {
      if (line.startsWith('SUMMARY:')) {
        currentEvent.title = line.replace('SUMMARY:', '').trim();
      } else if (line.startsWith('LOCATION:')) {
        currentEvent.location = line.replace('LOCATION:', '').trim();
      } else if (line.startsWith('DESCRIPTION:')) {
        currentEvent.description = line.replace('DESCRIPTION:', '').trim();
      } else if (line.startsWith('DTSTART')) {
        const val = line.split(':')[1];
        if (val && val.length >= 8) {
          const y = val.substring(0, 4);
          const m = val.substring(4, 6);
          const d = val.substring(6, 8);
          currentEvent.date = `${y}-${m}-${d}`;
          if (val.includes('T')) {
            const timePart = val.split('T')[1].replace('Z', '');
            currentEvent.time = `${timePart.substring(0, 2)}:${timePart.substring(2, 4)}`;
          }
        }
      }
    }
  }
  return events;
}

// One-Click Realistic GCal Sync for Japan Trip
function syncSampleFlightAndTrainEvents() {
  const sampleEvents = [
    {
      id: "ev-flight-in",
      title: "✈️ Flight to Tokyo (Haneda) NH204",
      date: "2026-11-09",
      time: "15:45 - 17:00",
      location: "Haneda Airport Terminal 3, Tokyo",
      category: "flight",
      description: "Flight arriving at Haneda Airport. Pick up Pocket WiFi / IC Card and take Tokyo Monorail."
    },
    {
      id: "ev-train-osaka",
      title: "Train to Shin-Osaka",
      date: "2026-11-10",
      time: "10:15 - 12:45",
      location: "Tokyo Station Shinkansen Platform 14",
      category: "transport",
      description: "Nozomi Shinkansen to Shin-Osaka. Oversized baggage reserved in Car 16, Row 17. ~2h30m journey with Mt. Fuji views on the right side."
    },
    {
      id: "ev-train-koya",
      title: "🚞 Nankai Koya Limited Express (Namba ➔ Gokurakubashi)",
      date: "2026-11-12",
      time: "09:00 - 10:25",
      location: "Nankai Namba Station",
      category: "transport",
      description: "Transfer to Koyasan Cable Car at Gokurakubashi. Koyasan World Heritage Pass valid."
    },
    {
      id: "ev-train-kanazawa",
      title: "🚆 JR Thunderbird Limited Express (Kyoto ➔ Kanazawa)",
      date: "2026-11-17",
      time: "09:40 - 11:50",
      location: "Kyoto Station Track 0",
      category: "transport",
      description: "Scenic ride along Lake Biwa into Hokuriku region. Reserved seats Car 4."
    },
    {
      id: "ev-train-tokyo-ret",
      title: "🚄 Hokuriku Shinkansen (Toyama ➔ Tokyo)",
      date: "2026-11-20",
      time: "17:30 - 21:00",
      location: "Toyama Station Track 12",
      category: "transport",
      description: "Hakutaka Shinkansen direct to Tokyo Station, then transfer to Ikebukuro."
    },
    {
      id: "ev-flight-out",
      title: "✈️ Departure Flight Haneda NH203",
      date: "2026-11-24",
      time: "15:45 - 17:00",
      location: "Haneda Airport International Terminal 3",
      category: "flight",
      description: "Departing Japan. Check in at least 2.5 hours prior. Duty Free shopping in Edo Ko-ji."
    }
  ];

  customCalendarEvents = sampleEvents;
  localStorage.setItem('japan_trip_calendar_events', JSON.stringify(customCalendarEvents));
  updateSyncButtonState();
  renderCurrentDay();
  closeModals();
  alert("✨ Successfully synced flights & train events to your offline schedule without duplicates!");
}

// 8. Event Listeners Setup
function setupEventListeners() {
  // Day navigation tap
  daysNavEl.addEventListener('click', (e) => {
    const pill = e.target.closest('.day-pill');
    if (pill) {
      currentDayIndex = parseInt(pill.dataset.day, 10);
      renderDaysNav();
      renderCurrentDay();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  });

  // Check off activity
  dayContentEl.addEventListener('click', (e) => {
    const checkBtn = e.target.closest('.check-btn');
    if (checkBtn) {
      const id = checkBtn.dataset.id;
      completedItems[id] = !completedItems[id];
      localStorage.setItem('japan_trip_completed', JSON.stringify(completedItems));
      renderCurrentDay();
    }
  });

  // Filter chips
  document.querySelectorAll('.filter-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      currentFilter = chip.dataset.filter;
      renderCurrentDay();
    });
  });

  // Calendar sync button opens modal
  syncStatusBtnEl.addEventListener('click', () => {
    calModalEl.classList.add('open');
  });

  // Handbook button opens modal
  document.getElementById('handbook-btn').addEventListener('click', () => {
    populateHandbookModal();
    handbookModalEl.classList.add('open');
  });

  // Bottom Navigation tabs
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      switchTab(tab.dataset.tab);
    });
  });

  // Modal Close buttons
  document.querySelectorAll('.btn-close, .modal-overlay').forEach(el => {
    el.addEventListener('click', (e) => {
      if (e.target === el || e.target.classList.contains('btn-close')) {
        closeModals();
        document.querySelectorAll('.nav-tab').forEach(t => {
          t.classList.toggle('active', t.dataset.tab === currentTab);
        });
      }
    });
  });

  // Prevent click propagation inside modal sheet
  document.querySelectorAll('.modal-sheet').forEach(sheet => {
    sheet.addEventListener('click', e => e.stopPropagation());
  });

  // Quick One-Click Sync
  document.getElementById('btn-oneclick-sync').addEventListener('click', syncSampleFlightAndTrainEvents);

  // ICS File Upload
  document.getElementById('ics-file-input').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const parsed = parseIcsFeed(event.target.result);
        if (parsed.length > 0) {
          customCalendarEvents = [...customCalendarEvents, ...parsed];
          localStorage.setItem('japan_trip_calendar_events', JSON.stringify(customCalendarEvents));
          updateSyncButtonState();
          renderCurrentDay();
          closeModals();
          alert(`✨ Successfully imported ${parsed.length} events from calendar file!`);
        } else {
          alert('No compatible events found in .ics file.');
        }
      };
      reader.readAsText(file);
    }
  });

  // ICS URL Sync
  document.getElementById('btn-sync-url').addEventListener('click', async () => {
    const urlInput = document.getElementById('ics-url-input').value.trim();
    if (!urlInput) {
      alert('Please enter an iCal (.ics) URL.');
      return;
    }
    try {
      const res = await fetch(urlInput);
      const text = await res.text();
      const parsed = parseIcsFeed(text);
      if (parsed.length > 0) {
        customCalendarEvents = parsed;
        localStorage.setItem('japan_trip_calendar_events', JSON.stringify(customCalendarEvents));
        updateSyncButtonState();
        renderCurrentDay();
        closeModals();
        alert(`✨ Successfully synced ${parsed.length} events from calendar feed!`);
      } else {
        alert('Could not find VEVENT entries in the response.');
      }
    } catch (err) {
      alert('Could not fetch calendar URL directly due to CORS. Tip: Download the .ics file and use the "Upload .ics File" option below!');
    }
  });
}

function closeModals() {
  document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('open'));
}

function populateHandbookModal() {
  const contentEl = document.getElementById('handbook-content');
  if (!itineraryData || !itineraryData.travel_handbook) return;

  const hb = itineraryData.travel_handbook;
  contentEl.innerHTML = `
    <h4 style="margin: 12px 0 6px 0; color: #38bdf8;">🚆 Transportation Rules & Passes</h4>
    <div style="display: flex; flex-direction: column; gap: 8px;">
      ${hb.transport_tips.map(t => `
        <div style="background: var(--bg-card); padding: 10px; border-radius: var(--radius-sm); border-left: 3px solid #38bdf8;">
          <strong style="color: #ffffff; font-size: 0.85rem;">${escapeHtml(t.title)}</strong>
          <p style="font-size: 0.78rem; color: #cbd5e1; margin-top: 4px;">${escapeHtml(t.detail)}</p>
        </div>
      `).join('')}
    </div>

    <h4 style="margin: 16px 0 6px 0; color: #a7f3d0;">📱 Essential Travel Apps</h4>
    <div style="display: flex; flex-direction: column; gap: 8px;">
      ${hb.essential_apps.map(a => `
        <div style="background: var(--bg-card); padding: 8px 10px; border-radius: var(--radius-sm); display: flex; justify-content: space-between; align-items: center;">
          <div>
            <strong style="color: #ffffff; font-size: 0.85rem;">${escapeHtml(a.name)}</strong>
            <div style="font-size: 0.76rem; color: #94a3b8;">${escapeHtml(a.desc)}</div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('./sw.js')
        .then(reg => console.log('[SW] ServiceWorker registered with scope:', reg.scope))
        .catch(err => console.warn('[SW] Registration failed:', err));
    });
  }
}

// Start
document.addEventListener('DOMContentLoaded', initApp);

// app.js - Mobile-First Japan PWA Engine
let itineraryData = null;
let currentDayIndex = 1;
let currentFilter = 'all';
let completedItems = JSON.parse(localStorage.getItem('japan_trip_completed') || '{}');
let customCalendarEvents = JSON.parse(localStorage.getItem('japan_trip_calendar_events') || '[]');

// DOM Elements
const daysNavEl = document.getElementById('days-nav');
const dayContentEl = document.getElementById('day-content');
const searchInputEl = document.getElementById('search-input');
const calModalEl = document.getElementById('calendar-modal');
const handbookModalEl = document.getElementById('handbook-modal');
const syncStatusBtnEl = document.getElementById('sync-status-btn');

// Initialize App
async function initApp() {
  registerServiceWorker();
  await loadItineraryData();
  renderDaysNav();
  renderCurrentDay();
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
        <span class="dp-city">${day.city}</span>
      </div>
    `;
  }).join('');

  // Scroll active pill into view
  const activePill = daysNavEl.querySelector('.day-pill.active');
  if (activePill) {
    activePill.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
  }
}

// 3. Render Current Selected Day
function renderCurrentDay() {
  if (!itineraryData) return;

  const day = itineraryData.days.find(d => d.day_index === currentDayIndex);
  if (!day) return;

  // Merge calendar events synced to this date
  const dayDate = day.date;
  const mergedItems = [...day.items];

  // Add any synced calendar events matching this date
  const matchedCalEvents = customCalendarEvents.filter(ev => ev.date === dayDate);
  matchedCalEvents.forEach(cal => {
    // Avoid exact duplicate
    if (!mergedItems.some(it => it.title === cal.title)) {
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
        opening_hours: cal.time ? `Scheduled: ${cal.time}` : null,
        user_notes: cal.description || 'Synced from Google Calendar',
        is_calendar_event: true,
        calendar_event: {
          synced: true,
          time_start: cal.time
        }
      });
    }
  });

  // Filter items
  const filteredItems = mergedItems.filter(item => {
    if (currentFilter === 'all') return true;
    if (currentFilter === 'attraction') return item.category === 'attraction';
    if (currentFilter === 'restaurant') return item.category === 'restaurant' || item.category === 'cafe';
    if (currentFilter === 'transport') return item.category === 'transport' || item.category === 'flight';
    if (currentFilter === 'shopping') return item.category === 'shopping';
    return true;
  });

  // Find next pending item
  const nextItem = filteredItems.find(it => !completedItems[it.id]);

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

  // Tailored Recommendations
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
      <div class="recommendations-card">
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

  // Items List HTML
  const itemsHtml = filteredItems.length > 0 ? filteredItems.map(item => {
    const isDone = !!completedItems[item.id];
    const catClass = `cat-${item.category || 'other'}`;

    return `
      <div class="itinerary-card ${isDone ? 'completed' : ''}" id="card-${item.id}">
        <div class="card-top">
          <div>
            <div class="card-badges">
              ${item.scheduled_time ? `<span class="time-badge">⏰ ${escapeHtml(item.scheduled_time)}</span>` : ''}
              <span class="category-badge ${catClass}">${item.category || 'Activity'}</span>
              ${item.is_calendar_event ? `<span class="category-badge" style="background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid #10b981;">📅 G-Cal Sync</span>` : ''}
            </div>
            <div class="card-title">${escapeHtml(item.title)}</div>
            ${item.pacing_note ? `<div class="pacing-tag">⏳ ${escapeHtml(item.pacing_note)}</div>` : ''}
            ${item.tagline ? `<div class="card-tagline">“${escapeHtml(item.tagline)}”</div>` : ''}
          </div>
          <button class="check-btn ${isDone ? 'checked' : ''}" data-id="${item.id}" title="Mark completed">
            ${isDone ? '✓' : ''}
          </button>
        </div>

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
  }).join('') : `
    <div style="padding: 24px; text-align: center; color: #94a3b8; background: var(--bg-surface); border-radius: var(--radius-md); border: 1px dashed var(--border-subtle);">
      No items match the selected category.
    </div>
  `;

  // Render Day container
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

    ${recsHtml}

    <div class="section-title-row">
      <h3 class="section-title">Day Schedule (${filteredItems.length} items)</h3>
      <span style="font-size: 0.75rem; color: #64748b;">Tap circle to check off</span>
    </div>

    <div class="timeline-list">
      ${itemsHtml}
    </div>
  `;
}

// 4. Calendar Sync Handlers
function updateSyncButtonState() {
  if (customCalendarEvents.length > 0) {
    syncStatusBtnEl.classList.add('synced');
    syncStatusBtnEl.innerHTML = `📅 Synced (${customCalendarEvents.length})`;
  } else {
    syncStatusBtnEl.classList.remove('synced');
    syncStatusBtnEl.innerHTML = `📅 Sync Calendar`;
  }
}

// Parse ICS text
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
          // Format: 20261110 or 20261110T090000Z
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

// 5. Sample / One-Click Realistic GCal Sync for Japan Trip
function syncSampleFlightAndTrainEvents() {
  const sampleEvents = [
    {
      id: "ev-flight-in",
      title: "✈️ Flight to Tokyo (Haneda) NH204",
      date: "2026-11-09",
      time: "15:45 Arrival",
      location: "Haneda Airport Terminal 3, Tokyo",
      category: "flight",
      description: "Flight arriving at Haneda Airport. Pick up Pocket WiFi / IC Card and take Tokyo Monorail."
    },
    {
      id: "ev-train-osaka",
      title: "🚄 Tokaido Shinkansen (Tokyo ➔ Shin-Osaka)",
      date: "2026-11-10",
      time: "10:15 - 12:45",
      location: "Tokyo Station Shinkansen Track 14",
      category: "transport",
      description: "Nozomi Shinkansen. Oversized baggage reserved in Car 16, Row 17."
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
      time: "16:20 - 18:35",
      location: "Toyama Station Track 12",
      category: "transport",
      description: "Hakutaka Shinkansen direct to Tokyo Station, then transfer to Ikebukuro."
    },
    {
      id: "ev-flight-out",
      title: "✈️ Departure Flight Haneda NH203",
      date: "2026-11-24",
      time: "18:20 Departure",
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
  alert("✨ Successfully synced flights & train events to your offline schedule!");
}

// 6. UI Helpers & Event Listeners
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

  // Bottom Nav
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      const tabName = tab.dataset.tab;
      document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      if (tabName === 'itinerary') {
        closeModals();
      } else if (tabName === 'sync') {
        calModalEl.classList.add('open');
      } else if (tabName === 'guide') {
        populateHandbookModal();
        handbookModalEl.classList.add('open');
      }
    });
  });

  // Modal Close buttons
  document.querySelectorAll('.btn-close, .modal-overlay').forEach(el => {
    el.addEventListener('click', (e) => {
      if (e.target === el || e.target.classList.contains('btn-close')) {
        closeModals();
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

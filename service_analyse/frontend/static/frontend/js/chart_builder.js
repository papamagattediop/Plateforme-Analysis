/* ================================================================
   CensusAnalyse — chart_builder.js
   Utilitaires globaux partagés entre cartes et dashboard
   ================================================================ */

/* ── API helpers ──────────────────────────────────────────── */

function getCsrfToken() {
  return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
}

async function apiGet(url) {
  const r = await fetch(url);
  if (!r.ok) {
    const e = await r.json().catch(() => ({}));
    throw new Error(e.error || `Erreur ${r.status}`);
  }
  return r.json();
}

async function apiPost(url, data) {
  const r = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify(data),
  });
  if (!r.ok) {
    const e = await r.json().catch(() => ({}));
    throw new Error(e.error || JSON.stringify(e) || `Erreur ${r.status}`);
  }
  return r.json();
}

async function apiDelete(url) {
  const r = await fetch(url, {
    method: 'DELETE',
    headers: { 'X-CSRFToken': getCsrfToken() },
  });
  if (!r.ok) throw new Error(`Erreur ${r.status}`);
  return true;
}

/* ── Toast system ─────────────────────────────────────────── */

const ICONS = {
  success: '<svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>',
  error:   '<svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
  info:    '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
};

function showToast(message, type = 'info', duration = 3500) {
  const root = document.getElementById('toast-root');
  if (!root) return;

  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `${ICONS[type] || ICONS.info}<span>${message}</span>`;
  root.appendChild(el);

  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(6px)';
    el.style.transition = '0.2s ease';
    setTimeout(() => el.remove(), 200);
  }, duration);
}

// Alias
function showNotification(message, type = 'info') {
  showToast(message, type);
}

/* ── Loading helpers ──────────────────────────────────────── */

function setLoading(id, on) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('hidden', !on);
}

/* ── Folium iframe ────────────────────────────────────────── */

function afficherCarteFolium(containerId, htmlFolium) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const ph = container.querySelector('.ph-block');
  if (ph) ph.classList.add('hidden');

  const old = container.querySelector('iframe.folium-frame');
  if (old) old.remove();

  const iframe = document.createElement('iframe');
  iframe.className = 'folium-frame';
  iframe.srcdoc = htmlFolium;
  iframe.style.cssText = 'width:100%;height:100%;min-height:520px;border:none;display:block;';
  container.style.alignItems = 'stretch';
  container.appendChild(iframe);
}

/* ── Share bar ────────────────────────────────────────────── */

function afficherShareBar(shareToken, type = 'cartes') {
  const url = `${window.location.origin}/${type}/share/${shareToken}/`;
  const bar = document.getElementById('share-bar');
  const input = document.getElementById('share-input');
  const openLink = document.getElementById('share-open');

  if (bar && input) {
    input.value = url;
    bar.classList.remove('hidden');
  }

  if (openLink) openLink.href = url;
  return url;
}

function copierShareLink() {
  const input = document.getElementById('share-input');
  if (!input) return;

  navigator.clipboard.writeText(input.value)
    .then(() => showToast('Lien copié dans le presse-papiers', 'success'))
    .catch(() => {
      input.select();
      document.execCommand('copy');
      showToast('Lien copié !', 'success');
    });
}
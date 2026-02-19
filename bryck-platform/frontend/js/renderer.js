/**
 * Pure DOM renderer.
 * Functions receive state and mutate the DOM. No side effects beyond DOM.
 */

import { store } from './store.js';

// ── Helpers ─────────────────────────────────

function statusBadge(status) {
  const map = {
    Active: 'active', Ready: 'ready', Down: 'down',
    Shipped: 'shipped', Decommissioned: 'decommissioned',
  };
  const cls = map[status] || 'unknown';
  return `<span class="badge badge--${cls}">${status}</span>`;
}

function healthBadge(health) {
  const map = {
    Healthy: 'healthy', Degraded: 'degraded',
    Unreachable: 'unreachable', Unknown: 'unknown',
  };
  const cls = map[health] || 'unknown';
  return `<span class="badge badge--health-${cls}">${health}</span>`;
}

function usageBadge(usage) {
  const map = {
    Testing: 'testing', Development: 'development',
    Customer: 'customer', Idle: 'idle',
  };
  const cls = map[usage] || 'idle';
  return `<span class="badge badge--usage-${cls}">${usage}</span>`;
}

function fmtDate(iso) {
  if (!iso) return '<span class="text-muted">—</span>';
  const d = new Date(iso);
  return d.toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' });
}

function escHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Table ────────────────────────────────────

export function renderTable() {
  const { machines, loading, error, editingCellId, editingField } = store.getState();
  const tbody = document.getElementById('machine-tbody');
  if (!tbody) return;

  if (loading) {
    tbody.innerHTML = `<tr><td colspan="11" class="table-empty">Loading…</td></tr>`;
    return;
  }
  if (error) {
    tbody.innerHTML = `<tr><td colspan="11" class="table-empty" style="color:var(--status-down)">${escHtml(error)}</td></tr>`;
    return;
  }
  if (!machines.length) {
    tbody.innerHTML = `<tr><td colspan="11" class="table-empty">No machines found.</td></tr>`;
    return;
  }

  tbody.innerHTML = machines.map(m => renderRow(m, editingCellId, editingField)).join('');
}

function renderRow(m, editingCellId, editingField) {
  const isEditing = editingCellId === m.id;

  const allottedCell = isEditing && editingField === 'allotted_to'
    ? `<div class="cell-editable">
         <input class="cell-edit-input" data-id="${m.id}" data-field="allotted_to"
                value="${escHtml(m.allotted_to || '')}" />
         <div class="cell-edit-actions">
           <button class="btn--icon" data-action="inline-save" data-id="${m.id}">✓</button>
           <button class="btn--icon" data-action="inline-cancel">✕</button>
         </div>
       </div>`
    : `<span class="cell-clickable" data-action="inline-edit"
             data-id="${m.id}" data-field="allotted_to"
             title="Click to edit">${escHtml(m.allotted_to) || '<span class="text-muted">—</span>'}</span>`;

  const statusCell = isEditing && editingField === 'status'
    ? `<div class="cell-editable">
         <select class="cell-edit-select" data-id="${m.id}" data-field="status">
           ${['Active','Ready','Down','Shipped'].map(s =>
             `<option${s === m.status ? ' selected' : ''}>${s}</option>`).join('')}
         </select>
         <div class="cell-edit-actions">
           <button class="btn--icon" data-action="inline-save" data-id="${m.id}">✓</button>
           <button class="btn--icon" data-action="inline-cancel">✕</button>
         </div>
       </div>`
    : `<span data-action="inline-edit" data-id="${m.id}" data-field="status"
             style="cursor:pointer" title="Click to change status">${statusBadge(m.status)}</span>`;

  return `
    <tr data-machine-id="${m.id}">
      <td class="cell-ip mono">${escHtml(m.machine_ip)}</td>
      <td>${escHtml(m.machine_type)}</td>
      <td>${statusCell}</td>
      <td>${healthBadge(m.health_status)}</td>
      <td>${usageBadge(m.used_for)}</td>
      <td>${allottedCell}</td>
      <td class="mono">${m.current_build
        ? `<span class="text-muted">${escHtml(m.current_build)}</span>`
        : '<span class="text-muted">—</span>'}</td>
      <td>${m.tests_completed ?? 0}</td>
      <td style="text-align:center">${m.can_run_parallel ? '✓' : '—'}</td>
      <td class="text-muted">${fmtDate(m.last_checked_at)}</td>
      <td>
        <div style="display:flex;gap:4px">
          <button class="btn--icon" data-action="edit" data-id="${m.id}" title="Edit">✎</button>
          <button class="btn--icon" data-action="health-check" data-id="${m.id}" title="Health Check">⚡</button>
          <button class="btn--icon" data-action="delete" data-id="${m.id}" title="Decommission"
                  style="color:var(--status-down)">⊗</button>
        </div>
      </td>
    </tr>
  `;
}

// ── Stats bar ────────────────────────────────

export function renderStats() {
  const { machines } = store.getState();
  const bar = document.getElementById('stats-bar');
  if (!bar) return;

  const counts = {};
  for (const m of machines) {
    counts[m.status] = (counts[m.status] || 0) + 1;
  }

  const pills = [
    { label: 'Active',        key: 'Active',        color: 'var(--status-active)' },
    { label: 'Ready',         key: 'Ready',         color: 'var(--status-ready)' },
    { label: 'Down',          key: 'Down',          color: 'var(--status-down)' },
    { label: 'Shipped',       key: 'Shipped',       color: 'var(--status-shipped)' },
    { label: 'Decommissioned',key: 'Decommissioned',color: 'var(--status-decommissioned)' },
  ];

  bar.innerHTML = pills
    .filter(p => counts[p.key])
    .map(p => `
      <div class="stat-pill">
        <span class="stat-pill__dot" style="background:${p.color}"></span>
        <span>${p.label}</span>
        <span class="stat-pill__count">${counts[p.key]}</span>
      </div>`)
    .join('') + `
      <div class="stat-pill">
        <span>Total</span>
        <span class="stat-pill__count">${store.getState().total}</span>
      </div>`;
}

// ── Pagination ───────────────────────────────

export function renderPagination() {
  const { page, pages, total } = store.getState();
  const el = document.getElementById('pagination');
  if (!el) return;

  if (pages <= 1) { el.innerHTML = ''; return; }

  const prevDisabled = page <= 1 ? 'disabled' : '';
  const nextDisabled = page >= pages ? 'disabled' : '';

  el.innerHTML = `
    <button class="page-btn" data-page="${page - 1}" ${prevDisabled}>‹ Prev</button>
    <span class="page-info">Page ${page} of ${pages} (${total} total)</span>
    <button class="page-btn" data-page="${page + 1}" ${nextDisabled}>Next ›</button>
  `;
}

// ── Modal form ───────────────────────────────

export function openModal(machine = null) {
  const overlay = document.getElementById('modal-overlay');
  const title   = document.getElementById('modal-title');
  const form    = document.getElementById('machine-form');

  title.textContent = machine ? 'Edit Machine' : 'Add Machine';
  form.reset();
  form.dataset.editId = machine ? machine.id : '';

  if (machine) {
    const fields = [
      'machine_ip','machine_type','status','used_for',
      'allotted_to','current_build','customer_name','active_issues','notes',
    ];
    fields.forEach(f => {
      const el = form.elements[f];
      if (el) el.value = machine[f] ?? '';
    });
    form.elements['can_run_parallel'].checked = !!machine.can_run_parallel;
    if (machine.shipping_date) {
      const dt = new Date(machine.shipping_date);
      form.elements['shipping_date'].value = dt.toISOString().slice(0,16);
    }
    // IP is read-only on edit
    document.getElementById('f-ip').readOnly = true;
  } else {
    document.getElementById('f-ip').readOnly = false;
  }

  clearFormErrors();
  overlay.classList.remove('hidden');
  document.getElementById('f-ip').focus();
}

export function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
}

export function clearFormErrors() {
  document.querySelectorAll('.form-error').forEach(el => el.textContent = '');
}

export function setFormError(field, msg) {
  const el = document.getElementById(`err-${field}`);
  if (el) el.textContent = msg;
}

// ── Confirm modal ────────────────────────────

export function openConfirm(message) {
  return new Promise(resolve => {
    const overlay = document.getElementById('confirm-overlay');
    document.getElementById('confirm-message').textContent = message;
    overlay.classList.remove('hidden');

    const ok = document.getElementById('btn-confirm-ok');
    const cancel = document.getElementById('btn-confirm-cancel');
    const close  = document.getElementById('btn-confirm-close');

    function cleanup(result) {
      overlay.classList.add('hidden');
      ok.replaceWith(ok.cloneNode(true));
      cancel.replaceWith(cancel.cloneNode(true));
      close.replaceWith(close.cloneNode(true));
      resolve(result);
    }

    document.getElementById('btn-confirm-ok').addEventListener('click', () => cleanup(true), { once: true });
    document.getElementById('btn-confirm-cancel').addEventListener('click', () => cleanup(false), { once: true });
    document.getElementById('btn-confirm-close').addEventListener('click', () => cleanup(false), { once: true });
  });
}

// ── Toast ────────────────────────────────────

export function toast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast toast--${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

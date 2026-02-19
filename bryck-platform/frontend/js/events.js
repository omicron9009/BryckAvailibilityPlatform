/**
 * Event wiring module.
 * Uses event delegation on high-level containers.
 * No direct DOM coupling to specific rows/cells.
 */

import { store } from './store.js';
import { API, APIError } from './api.js';
import {
  renderTable, renderStats, renderPagination,
  openModal, closeModal, openConfirm, toast,
  setFormError, clearFormErrors,
} from './renderer.js';
import { loadMachines } from './app.js';

// ── Table action delegation ──────────────────

export function bindTableEvents() {
  const tbody = document.getElementById('machine-tbody');

  tbody.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const action = btn.dataset.action;
    const id = btn.dataset.id;

    switch (action) {
      case 'edit':        return handleEdit(id);
      case 'delete':      return handleDelete(id);
      case 'health-check':return handleHealthCheck(id);
      case 'inline-edit': return handleInlineEditStart(btn.dataset.id, btn.dataset.field);
      case 'inline-save': return handleInlineSave(id);
      case 'inline-cancel': return handleInlineCancel();
    }
  });
}

async function handleEdit(id) {
  try {
    const machine = await API.machines.get(id);
    openModal(machine);
  } catch (err) {
    toast(err.detail || 'Failed to load machine.', 'error');
  }
}

async function handleDelete(id) {
  const { machines } = store.getState();
  const machine = machines.find(m => m.id === id);
  const confirmed = await openConfirm(
    `Decommission machine ${machine?.machine_ip || id}? This cannot be undone easily.`
  );
  if (!confirmed) return;

  try {
    await API.machines.delete(id);
    toast('Machine decommissioned.', 'success');
    await loadMachines();
  } catch (err) {
    toast(err.detail || 'Failed to decommission.', 'error');
  }
}

async function handleHealthCheck(id) {
  const { machines } = store.getState();
  const machine = machines.find(m => m.id === id);
  toast(`Running health check on ${machine?.machine_ip || id}…`, 'info');
  try {
    const result = await API.machines.healthCheck(id);
    toast(
      `${result.machine_ip}: ${result.health_status} — Build: ${result.current_build || 'N/A'}`,
      result.is_reachable ? 'success' : 'error'
    );
    await loadMachines();
  } catch (err) {
    toast(err.detail || 'Health check failed.', 'error');
  }
}

function handleInlineEditStart(id, field) {
  store.setState({ editingCellId: id, editingField: field });
  renderTable();
  // Focus the new input
  setTimeout(() => {
    const input = document.querySelector(`[data-id="${id}"][data-field="${field}"]`);
    if (input) input.focus();
  }, 0);
}

async function handleInlineSave(id) {
  const { editingField } = store.getState();
  const input = document.querySelector(
    `.cell-edit-input[data-id="${id}"], .cell-edit-select[data-id="${id}"]`
  );
  if (!input) return;

  try {
    const updated = await API.machines.update(id, { [editingField]: input.value });
    store.setState({
      editingCellId: null,
      editingField: null,
      machines: store.getState().machines.map(m => m.id === id ? updated : m),
    });
    renderTable();
    renderStats();
    toast('Saved.', 'success');
  } catch (err) {
    toast(err.detail || 'Save failed.', 'error');
  }
}

function handleInlineCancel() {
  store.setState({ editingCellId: null, editingField: null });
  renderTable();
}

// ── Filter events ────────────────────────────

export function bindFilterEvents() {
  let debounceTimer;

  document.getElementById('filter-search').addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      store.setState({ filters: { ...store.getState().filters, search: e.target.value }, page: 1 });
      loadMachines();
    }, 300);
  });

  ['filter-status', 'filter-used-for', 'filter-type'].forEach(id => {
    document.getElementById(id).addEventListener('change', (e) => {
      const keyMap = {
        'filter-status': 'status',
        'filter-used-for': 'used_for',
        'filter-type': 'machine_type',
      };
      store.setState({
        filters: { ...store.getState().filters, [keyMap[id]]: e.target.value },
        page: 1,
      });
      loadMachines();
    });
  });

  document.getElementById('btn-clear-filters').addEventListener('click', () => {
    store.setState({ filters: { search:'', status:'', used_for:'', machine_type:'' }, page: 1 });
    document.getElementById('filter-search').value = '';
    document.getElementById('filter-status').value = '';
    document.getElementById('filter-used-for').value = '';
    document.getElementById('filter-type').value = '';
    loadMachines();
  });
}

// ── Pagination events ────────────────────────

export function bindPaginationEvents() {
  document.getElementById('pagination').addEventListener('click', (e) => {
    const btn = e.target.closest('[data-page]');
    if (!btn || btn.disabled) return;
    const p = parseInt(btn.dataset.page, 10);
    if (!isNaN(p)) {
      store.setState({ page: p });
      loadMachines();
    }
  });
}

// ── Modal / Form events ──────────────────────

export function bindModalEvents() {
  document.getElementById('btn-add-machine').addEventListener('click', () => openModal());
  document.getElementById('btn-modal-close').addEventListener('click', closeModal);
  document.getElementById('btn-form-cancel').addEventListener('click', closeModal);

  document.getElementById('modal-overlay').addEventListener('click', (e) => {
    if (e.target === document.getElementById('modal-overlay')) closeModal();
  });

  document.getElementById('machine-form').addEventListener('submit', handleFormSubmit);
}

async function handleFormSubmit(e) {
  e.preventDefault();
  clearFormErrors();

  const form = e.target;
  const isEdit = !!form.dataset.editId;
  const id = form.dataset.editId;

  const data = {
    machine_ip:       form.elements['machine_ip'].value.trim(),
    machine_type:     form.elements['machine_type'].value,
    status:           form.elements['status'].value,
    used_for:         form.elements['used_for'].value,
    allotted_to:      form.elements['allotted_to'].value.trim() || null,
    current_build:    form.elements['current_build'].value.trim() || null,
    customer_name:    form.elements['customer_name'].value.trim() || null,
    active_issues:    form.elements['active_issues'].value.trim() || null,
    notes:            form.elements['notes'].value.trim() || null,
    can_run_parallel: form.elements['can_run_parallel'].checked,
    shipping_date:    form.elements['shipping_date'].value
                        ? new Date(form.elements['shipping_date'].value).toISOString()
                        : null,
  };

  const submitBtn = document.getElementById('btn-form-submit');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Saving…';

  try {
    if (isEdit) {
      await API.machines.update(id, data);
      toast('Machine updated.', 'success');
    } else {
      await API.machines.create(data);
      toast('Machine added.', 'success');
    }
    closeModal();
    await loadMachines();
  } catch (err) {
    if (err instanceof APIError) {
      if (err.status === 409) setFormError('ip', err.detail);
      else if (err.status === 422) toast('Validation error. Check fields.', 'error');
      else toast(err.detail || 'An error occurred.', 'error');
    } else {
      toast('Network error. Is the backend running?', 'error');
    }
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Save';
  }
}

// ── Toolbar events ───────────────────────────

export function bindToolbarEvents() {
  document.getElementById('btn-refresh').addEventListener('click', () => loadMachines());

  let autoTimer = null;
  document.getElementById('chk-auto-refresh').addEventListener('change', (e) => {
    if (e.target.checked) {
      autoTimer = setInterval(() => loadMachines(), 30_000);
      toast('Auto-refresh enabled (30s).', 'info');
    } else {
      clearInterval(autoTimer);
      toast('Auto-refresh disabled.', 'info');
    }
  });
}

/**
 * Application entry point.
 * Bootstraps store, wires events, performs initial data load.
 */

import { store } from './store.js';
import { API } from './api.js';
import {
  renderTable, renderStats, renderPagination,
} from './renderer.js';
import {
  bindTableEvents,
  bindFilterEvents,
  bindPaginationEvents,
  bindModalEvents,
  bindToolbarEvents,
} from './events.js';

// ── Core data loader ─────────────────────────

export async function loadMachines() {
  const { filters, page, pageSize } = store.getState();

  store.setState({ loading: true, error: null });
  renderTable();

  try {
    const data = await API.machines.list({
      ...filters,
      page,
      page_size: pageSize,
    });
    store.setState({
      machines: data.items,
      total: data.total,
      pages: data.pages,
      loading: false,
    });
  } catch (err) {
    store.setState({
      loading: false,
      error: err.detail || 'Failed to connect to backend.',
    });
  }

  renderTable();
  renderStats();
  renderPagination();
}

// ── Bootstrap ────────────────────────────────

function init() {
  bindTableEvents();
  bindFilterEvents();
  bindPaginationEvents();
  bindModalEvents();
  bindToolbarEvents();
  loadMachines();
}

document.addEventListener('DOMContentLoaded', init);

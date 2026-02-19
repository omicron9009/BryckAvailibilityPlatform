/**
 * Minimal reactive store.
 * Components subscribe to changes and re-render on demand.
 */

function createStore(initialState) {
  let state = { ...initialState };
  const listeners = new Set();

  return {
    getState() {
      return state;
    },
    setState(partial) {
      state = { ...state, ...partial };
      listeners.forEach(fn => fn(state));
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn); // returns unsubscribe
    },
  };
}

export const store = createStore({
  machines: [],
  total: 0,
  page: 1,
  pageSize: 50,
  pages: 1,
  loading: false,
  error: null,
  filters: {
    search: '',
    status: '',
    used_for: '',
    machine_type: '',
  },
  editingCellId: null,   // machine id currently being inline-edited
  editingField: null,
});

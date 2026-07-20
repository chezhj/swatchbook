import { apiGet } from '../api.js';

/**
 * Log list (SCR-06) plus its filter sheet — the collection grid's pattern applied to
 * the log. The server renders the first page; this takes over as soon as a search,
 * filter or sort changes, refetching /api/log-entries/ and swapping the list.
 *
 * `polishId` carries the ?polish= deep link from the polish detail screen, so
 * filtering within "entries wearing X" keeps working once the client takes over.
 */
export default function logList(initialCount = 0, polishId = '') {
  return {
    sheetOpen: false,
    loading: false,
    error: '',
    search: '',
    formulas: [],
    colors: [],
    sort: '-date_worn',
    polishId,
    // null = server-rendered markup is still what's on screen.
    results: null,
    resultCount: initialCount,

    get activeFilterCount() {
      return this.formulas.length + this.colors.length;
    },

    toggle(list, value) {
      const index = this[list].indexOf(value);
      if (index === -1) this[list].push(value);
      else this[list].splice(index, 1);
      this.refresh();
    },

    isOn(list, value) {
      return this[list].includes(value);
    },

    setSort(value) {
      this.sort = value;
      this.refresh();
    },

    clearAll() {
      this.formulas = [];
      this.colors = [];
      this.search = '';
      this.sort = '-date_worn';
      this.refresh();
    },

    async refresh() {
      this.loading = true;
      this.error = '';
      try {
        const data = await apiGet('/api/log-entries/', {
          formula: this.formulas,
          color: this.colors,
          search: this.search,
          sort: this.sort,
          polish: this.polishId,
          page_size: 200,
        });
        this.results = data.results ?? data;
        this.resultCount = data.count ?? this.results.length;
      } catch (err) {
        this.error = `Couldn't load the log (${err.message}).`;
      } finally {
        this.loading = false;
      }
    },

    // "2026-07-12" → "12 JUL 2026", matching the server rows' date format.
    formatDate(iso) {
      return new Date(`${iso}T00:00:00`)
        .toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
        .toUpperCase();
    },

    init() {
      // Debounce the search box so typing doesn't fire a request per keystroke.
      let timer;
      this.$watch('search', () => {
        clearTimeout(timer);
        timer = setTimeout(() => this.refresh(), 250);
      });
    },
  };
}

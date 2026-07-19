import { apiGet } from '../api.js';

/**
 * Collection grid (SCR-01) plus the filter sheet (SCR-02).
 *
 * The server renders the first page so there is no empty flash; this takes over as
 * soon as a filter or sort changes, refetching /api/polishes/ and swapping the grid.
 */
export default function collectionGrid(initialCount = 0) {
  return {
    sheetOpen: false,
    loading: false,
    error: '',
    search: '',
    formulas: [],
    colors: [],
    sort: 'name',
    // null = server-rendered markup is still what's on screen.
    results: null,
    resultCount: initialCount,

    get isFiltered() {
      return this.formulas.length > 0 || this.colors.length > 0 || this.search !== '';
    },

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
      this.sort = 'name';
      this.refresh();
    },

    async refresh() {
      this.loading = true;
      this.error = '';
      try {
        const data = await apiGet('/api/polishes/', {
          formula: this.formulas,
          color: this.colors,
          search: this.search,
          sort: this.sort,
          in_collection: 'true',
          page_size: 200,
        });
        this.results = data.results ?? data;
        this.resultCount = data.count ?? this.results.length;
      } catch (err) {
        this.error = `Couldn't load polishes (${err.message}).`;
      } finally {
        this.loading = false;
      }
    },

    swatchClasses(polish) {
      const classes = ['swatch', ...(polish.finish_classes || [])];
      if ((polish.color_names || []).includes('Rainbow')) classes.push('is-rainbow');
      return classes.join(' ');
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

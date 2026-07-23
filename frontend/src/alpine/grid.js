import { apiGet } from '../api.js';

// Filter/sort/group choices survive a round-trip to a detail page and back, but not a
// new tab or a fresh visit — sessionStorage is exactly that lifetime.
const STORAGE_KEY = 'collectionGridState';
const DEFAULT_SORT = '-created_at';

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
    sort: DEFAULT_SORT,
    // 'none' | 'brand' | 'collection'. Purely a client-side view over `results` —
    // it re-partitions the fetched list, it doesn't change what we fetch.
    group: 'none',
    // null = server-rendered markup is still what's on screen.
    results: null,
    resultCount: initialCount,

    get isFiltered() {
      return this.formulas.length > 0 || this.colors.length > 0 || this.search !== '';
    },

    get activeFilterCount() {
      return this.formulas.length + this.colors.length;
    },

    // A flat list of render sections, whatever the grouping mode. Each section is a
    // grid of polishes with optional brand / collection headers; the template loops
    // over these once and never has to branch on `group`. Polishes keep the order the
    // API sorted them in — grouping only partitions, it never re-sorts within a group.
    get sections() {
      const list = this.results || [];
      if (this.group === 'none') {
        return [{ key: 'all', brandLabel: null, collLabel: null, collYear: null, polishes: list }];
      }
      if (this.group === 'brand') {
        return this.byBrand(list).map((b) => ({
          key: `b${b.id}`,
          brandLabel: b.name,
          collLabel: null,
          collYear: null,
          polishes: b.polishes,
        }));
      }
      // Collection: brands wrap collections, so the brand header prints once per brand
      // and each of its collections gets its own sub-header + grid beneath it.
      const out = [];
      for (const b of this.byBrand(list)) {
        this.byCollection(b.polishes).forEach((c, i) => {
          out.push({
            key: `b${b.id}c${c.id ?? 'none'}`,
            brandLabel: i === 0 ? b.name : null,
            collLabel: c.name,
            collYear: c.year,
            polishes: c.polishes,
          });
        });
      }
      return out;
    },

    // Bucket by brand, brands alphabetical. Members keep their incoming order.
    byBrand(list) {
      const map = new Map();
      for (const p of list) {
        if (!map.has(p.brand)) map.set(p.brand, { id: p.brand, name: p.brand_name, polishes: [] });
        map.get(p.brand).polishes.push(p);
      }
      return [...map.values()].sort((a, b) => a.name.localeCompare(b.name));
    },

    // Bucket by collection, newest year first (matching the Collection model default);
    // the "no collection" bucket sinks to the bottom.
    byCollection(list) {
      const map = new Map();
      for (const p of list) {
        const key = p.collection ?? 'none';
        if (!map.has(key)) {
          map.set(key, {
            id: p.collection,
            name: p.collection_name || 'No collection',
            year: p.collection_year ?? null,
            polishes: [],
          });
        }
        map.get(key).polishes.push(p);
      }
      return [...map.values()].sort((a, b) => {
        if (a.id == null) return 1;
        if (b.id == null) return -1;
        const ay = a.year ?? -Infinity;
        const by = b.year ?? -Infinity;
        return by - ay || a.name.localeCompare(b.name);
      });
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

    setGroup(value) {
      this.group = value;
      // Grouping partitions `results`, so it only needs a fetch when the server
      // markup is still what's on screen. Persist either way.
      if (this.results === null) this.refresh();
      else this.persist();
    },

    clearAll() {
      this.formulas = [];
      this.colors = [];
      this.search = '';
      this.sort = DEFAULT_SORT;
      this.group = 'none';
      this.refresh();
    },

    persist() {
      try {
        sessionStorage.setItem(
          STORAGE_KEY,
          JSON.stringify({
            search: this.search,
            formulas: this.formulas,
            colors: this.colors,
            sort: this.sort,
            group: this.group,
          }),
        );
      } catch {
        // Private-mode / quota errors: persistence is a nicety, not worth failing over.
      }
    },

    loadState() {
      try {
        const raw = sessionStorage.getItem(STORAGE_KEY);
        return raw ? JSON.parse(raw) : null;
      } catch {
        return null;
      }
    },

    async refresh() {
      this.persist();
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

    // The two below mirror web/templates/web/_swatch.html — keep them in step. A photo
    // is the face of the tile; the finish classes only decorate the empty placeholder.
    swatchClasses(polish) {
      if (polish.photo_url) return 'swatch';
      const classes = ['swatch', 'is-empty', ...(polish.finish_classes || [])];
      if ((polish.color_names || []).includes('Rainbow')) classes.push('is-rainbow');
      return classes.join(' ');
    },

    swatchStyle(polish) {
      return polish.photo_url ? `background-image: url('${polish.photo_url}')` : '';
    },

    init() {
      // Restore the choices from a previous page in this session before wiring up the
      // search watcher, so hydrating `search` doesn't itself trigger a debounced fetch.
      const saved = this.loadState();
      if (saved) {
        this.search = saved.search ?? '';
        this.formulas = saved.formulas ?? [];
        this.colors = saved.colors ?? [];
        this.sort = saved.sort ?? DEFAULT_SORT;
        this.group = saved.group ?? 'none';
      }

      // Debounce the search box so typing doesn't fire a request per keystroke.
      let timer;
      this.$watch('search', () => {
        clearTimeout(timer);
        timer = setTimeout(() => this.refresh(), 250);
      });

      // The server-rendered first paint is the default view; if we restored anything,
      // fetch to bring the grid in line with it.
      if (saved) this.refresh();
    },
  };
}

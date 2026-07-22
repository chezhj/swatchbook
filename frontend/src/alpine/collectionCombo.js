import { apiGet, apiSend } from '../api.js';

/**
 * The polish form's collection field: one control that searches a brand's existing
 * collections, creates a new one inline, or edits the chosen one.
 *
 * A collection belongs to exactly one brand, so everything here is scoped to whatever
 * brand the form has selected (existing dropdown or the "new brand" text box). The
 * component doesn't own that brand state — it reads it off those elements and reacts
 * to their changes.
 *
 * It writes to three hidden inputs the server already understands (see PolishForm):
 *   collectionId  — an existing collection's id, or empty
 *   newName/newYear — a collection to get_or_create on save, or empty
 * Only one route is ever populated at a time. Editing an *existing* collection is a
 * PATCH to the API, because it changes a shared record; editing a not-yet-saved one
 * just updates newName/newYear.
 */
export default function collectionCombo({ brandSelectId, newBrandId, selectedId = '' }) {
  return {
    brandId: '',
    brandLabel: '',
    query: '',
    open: false,
    loading: false,
    options: [],
    selected: null,
    editing: false,
    editName: '',
    editYear: '',
    error: '',

    init() {
      const brandSel = document.getElementById(brandSelectId);
      const newBrand = document.getElementById(newBrandId);
      const sync = () => this.syncBrand(brandSel, newBrand);
      if (brandSel) brandSel.addEventListener('change', sync);
      if (newBrand) newBrand.addEventListener('input', sync);

      if (selectedId) {
        // Name/year come from data-* attributes rather than the x-data literal: a
        // collection name like "Winter '24" would break a JS string but is fine in an
        // HTML attribute the browser hands back verbatim.
        const ds = this.$root.dataset;
        this.selected = {
          id: Number(selectedId),
          name: ds.selectedName || '',
          year: ds.selectedYear || null,
        };
      }
      this.syncBrand(brandSel, newBrand, true);
    },

    syncBrand(brandSel, newBrand, initial = false) {
      const id = brandSel && brandSel.value ? brandSel.value : '';
      const label =
        brandSel && brandSel.value
          ? brandSel.options[brandSel.selectedIndex].text.trim()
          : newBrand
            ? newBrand.value.trim()
            : '';
      const changed = id !== this.brandId;
      this.brandId = id;
      this.brandLabel = label;

      // Switching brand invalidates a collection chosen under the old one. Leave the
      // initial edit-mode selection alone — that collection matches its polish's brand.
      if (changed && !initial) this.clear();

      if (this.brandId) this.fetchOptions();
      else this.options = [];
    },

    get enabled() {
      return !!this.brandId || !!this.brandLabel;
    },

    get canList() {
      return !!this.brandId;
    },

    async fetchOptions() {
      this.loading = true;
      try {
        const data = await apiGet('/api/collections/', {
          brand: this.brandId,
          page_size: 200,
        });
        this.options = (data.results ?? data).map((c) => ({
          id: c.id,
          name: c.name,
          year: c.year,
        }));
      } catch (e) {
        this.options = [];
      } finally {
        this.loading = false;
      }
    },

    get filtered() {
      const q = this.query.trim().toLowerCase();
      if (!q) return this.options;
      return this.options.filter((o) => o.name.toLowerCase().includes(q));
    },

    get exactMatch() {
      const q = this.query.trim().toLowerCase();
      return !!q && this.options.some((o) => o.name.toLowerCase() === q);
    },

    get showCreate() {
      return this.enabled && !!this.query.trim() && !this.exactMatch;
    },

    // --- hidden-field writers: exactly one route is populated at a time ---
    writeExisting(opt) {
      this.$refs.collectionId.value = opt.id;
      this.$refs.newName.value = '';
      this.$refs.newYear.value = '';
    },
    writeNew(name, year) {
      this.$refs.collectionId.value = '';
      this.$refs.newName.value = name;
      this.$refs.newYear.value = year || '';
    },
    writeEmpty() {
      this.$refs.collectionId.value = '';
      this.$refs.newName.value = '';
      this.$refs.newYear.value = '';
    },

    choose(opt) {
      this.selected = { ...opt };
      this.writeExisting(opt);
      this.query = '';
      this.open = false;
    },

    createFromQuery() {
      const name = this.query.trim();
      if (!name) return;
      this.selected = { id: null, name, year: null, isNew: true };
      this.writeNew(name, null);
      this.query = '';
      this.open = false;
    },

    clear() {
      this.selected = null;
      this.editing = false;
      this.writeEmpty();
      this.query = '';
    },

    startEdit() {
      if (!this.selected) return;
      this.editName = this.selected.name;
      this.editYear = this.selected.year || '';
      this.error = '';
      this.editing = true;
    },

    cancelEdit() {
      this.editing = false;
      this.error = '';
    },

    async saveEdit() {
      const name = this.editName.trim();
      const year = this.editYear ? Number(this.editYear) : null;
      if (!name) {
        this.error = 'Give the collection a name.';
        return;
      }

      // Not saved yet: no record to PATCH, just update the pending create fields.
      if (this.selected.isNew) {
        this.selected.name = name;
        this.selected.year = year;
        this.writeNew(name, year);
        this.editing = false;
        return;
      }

      try {
        await apiSend(`/api/collections/${this.selected.id}/`, 'PATCH', { name, year });
        this.selected.name = name;
        this.selected.year = year;
        const opt = this.options.find((o) => o.id === this.selected.id);
        if (opt) {
          opt.name = name;
          opt.year = year;
        }
        this.writeExisting(this.selected);
        this.editing = false;
      } catch (e) {
        this.error = 'Couldn’t save — that name may already exist for this brand.';
      }
    },
  };
}

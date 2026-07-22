/**
 * The polish picker on one "polish worn" row of the log form.
 *
 * The catalog can hold hundreds of polishes, so a native <select> is unwieldy — this
 * is a type-to-search combobox instead. Unlike the collection combo it only *selects*:
 * no create, no edit. It writes the chosen polish id into the row's hidden field and
 * shows the picked polish as a token with a clear button.
 *
 * Options (id + label) are embedded once in the page as a json_script tag and shared
 * across every row, so filtering is instant and there's no per-row request.
 */
let cachedOptions = null;

function getOptions() {
  if (cachedOptions) return cachedOptions;
  const el = document.getElementById('polish-options');
  cachedOptions = el ? JSON.parse(el.textContent) : [];
  return cachedOptions;
}

// Only the id is passed in from the template (a pk — safe to inline); the label is
// looked up here, so a name containing a quote can't break the x-data attribute.
export default function polishSelect({ selectedId = '' } = {}) {
  return {
    query: '',
    open: false,
    options: [],
    selected: null,

    init() {
      this.options = getOptions();
      if (selectedId) {
        this.selected = this.options.find((o) => o.id === Number(selectedId)) || null;
      }
    },

    get filtered() {
      const q = this.query.trim().toLowerCase();
      const list = q
        ? this.options.filter((o) => o.label.toLowerCase().includes(q))
        : this.options;
      // Hundreds of polishes: cap what actually renders so a bare field isn't a wall.
      return list.slice(0, 50);
    },

    choose(opt) {
      this.selected = opt;
      this.$refs.polishId.value = opt.id;
      this.query = '';
      this.open = false;
    },

    clear() {
      this.selected = null;
      this.$refs.polishId.value = '';
      this.query = '';
    },
  };
}

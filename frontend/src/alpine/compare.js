/**
 * Compare picker (SCR-04). Tracks up to two selected polishes and builds the link
 * through to the result screen.
 */
const MAX_SELECTION = 2;

export default function compareSelection() {
  return {
    selected: [],

    isSelected(id) {
      return this.selected.some((p) => p.id === id);
    },

    toggle(id, name, hex) {
      const index = this.selected.findIndex((p) => p.id === id);
      if (index !== -1) {
        this.selected.splice(index, 1);
        return;
      }
      if (this.selected.length >= MAX_SELECTION) {
        // Drop the oldest so tapping a third swatch always feels responsive rather
        // than silently doing nothing.
        this.selected.shift();
      }
      this.selected.push({ id, name, hex });
    },

    get ready() {
      return this.selected.length === MAX_SELECTION;
    },

    get summary() {
      return this.selected.map((p) => p.name).join(' + ');
    },

    get compareUrl() {
      const params = new URLSearchParams();
      this.selected.forEach((p) => params.append('polish', p.id));
      return `/compare/result/?${params.toString()}`;
    },
  };
}

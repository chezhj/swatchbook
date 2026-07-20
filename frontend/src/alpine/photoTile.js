/**
 * One photo slot on the polish form.
 *
 * A polish's photos are its swatch, so the form leads with them and each slot shows
 * what you picked before you save — an object URL for a fresh file, the stored image
 * for one already on the record.
 */
export default function photoTile(saved = '') {
  return {
    saved,
    picked: '',
    removed: false,

    get preview() {
      return this.picked || this.saved;
    },

    get isEmpty() {
      return !this.preview;
    },

    pick(event) {
      const file = event.target.files[0];
      // Revoke the previous object URL rather than leaking one per re-pick.
      if (this.picked) URL.revokeObjectURL(this.picked);
      this.picked = file ? URL.createObjectURL(file) : '';
      if (file) this.removed = false;
    },

    destroy() {
      if (this.picked) URL.revokeObjectURL(this.picked);
    },
  };
}

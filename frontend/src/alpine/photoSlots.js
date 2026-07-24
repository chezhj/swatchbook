/**
 * The photo grid on the polish and log forms. Keeps the Django formset's TOTAL_FORMS in
 * sync and guarantees a trailing empty tile: the moment the last placeholder gets a
 * file, a fresh empty tile is appended, so photos can be added without saving first.
 *
 * New tiles are built from the formset's rendered empty_form (an inert <template> whose
 * ids/names carry a __prefix__ placeholder), not by cloning a live tile — a fresh
 * fragment from the pristine template gets initialised cleanly by Alpine, whereas a
 * clone would drag along an already-initialised photoTile's state.
 */
export default function photoSlots(prefix) {
  return {
    // A change bubbles up from any tile's file input. If the last tile now holds a
    // file, there is no empty placeholder left, so grow the grid by one. Appending
    // only ever fires off the last tile, so unrelated changes (Main/Remove toggles on
    // earlier tiles) can't spawn duplicates.
    reconcile() {
      const slots = this.$el.querySelectorAll('.photo-slot');
      const last = slots[slots.length - 1];
      const input = last && last.querySelector('input[type="file"]');
      if (input && input.files.length) this.addSlot();
    },

    addSlot() {
      const totalInput = document.querySelector(`#id_${prefix}-TOTAL_FORMS`);
      if (!totalInput) return;

      const index = parseInt(totalInput.value, 10);
      const html = this.$refs.tpl.innerHTML.replace(/__prefix__/g, index);
      this.$refs.tpl.insertAdjacentHTML('beforebegin', html);
      totalInput.value = index + 1;
    },
  };
}

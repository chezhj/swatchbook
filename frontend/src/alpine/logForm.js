/**
 * Log entry form. Django inline formsets need the management form's TOTAL_FORMS kept
 * in sync when rows are added client-side.
 *
 * New rows are built from each formset's rendered empty_form (an inert <template> whose
 * ids/names carry a __prefix__ placeholder), not by cloning an existing row. A polish
 * row is an Alpine component, and cloning a live one would drag along its initialised
 * state and duplicate its x-for output; a fresh fragment from the pristine template
 * gets initialised cleanly by Alpine instead.
 */
export default function logEntryForm() {
  return {
    addRow(prefix) {
      const template = document.getElementById(`${prefix}-empty`);
      const container = this.$refs[`${prefix}Rows`];
      const totalInput = document.querySelector(`#id_${prefix}-TOTAL_FORMS`);
      if (!template || !container || !totalInput) return;

      const index = parseInt(totalInput.value, 10);
      const html = template.innerHTML.replace(/__prefix__/g, index);
      container.appendChild(document.createRange().createContextualFragment(html));
      totalInput.value = index + 1;
    },
  };
}

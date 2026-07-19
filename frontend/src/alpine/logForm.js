/**
 * Log entry form. Django inline formsets need the management form's TOTAL_FORMS kept
 * in sync when rows are added client-side; this does that and nothing more.
 */
export default function logEntryForm() {
  return {
    addRow(prefix) {
      const container = this.$refs[`${prefix}Rows`];
      const totalInput = document.querySelector(`#id_${prefix}-TOTAL_FORMS`);
      if (!container || !totalInput) return;

      const template = container.querySelector('.formset-row');
      if (!template) return;

      const index = parseInt(totalInput.value, 10);
      const clone = template.cloneNode(true);

      clone.querySelectorAll('input, select, textarea').forEach((field) => {
        if (field.name) field.name = field.name.replace(/-\d+-/, `-${index}-`);
        if (field.id) field.id = field.id.replace(/-\d+-/, `-${index}-`);
        if (field.type === 'checkbox') field.checked = false;
        else if (field.type !== 'hidden') field.value = '';
        else if (field.name.endsWith('-id')) field.value = '';
      });
      clone.querySelectorAll('label').forEach((label) => {
        if (label.htmlFor) label.htmlFor = label.htmlFor.replace(/-\d+-/, `-${index}-`);
      });

      container.appendChild(clone);
      totalInput.value = index + 1;
    },
  };
}

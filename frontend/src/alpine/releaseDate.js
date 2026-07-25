/**
 * The polish form's release-date row. Year is mandatory (enforced server-side too);
 * month and day are optional. On top of the plain inputs it surfaces two live, styled
 * messages so the user isn't left guessing after a blocked submit:
 *
 *   dateError — a blocking problem with the date itself: an out-of-range month or day,
 *               a day with no month, or an impossible date like 31 Feb. Mirrors the
 *               server-side checks in PolishForm.clean() so the feedback is immediate.
 *   mismatch  — a non-blocking heads-up that the release year disagrees with the
 *               chosen collection's year (from the shared store collectionCombo writes).
 *
 * The three inputs keep `year` / `month` / `day` in step via `@input` (see the widget
 * attrs in PolishForm); the initial values are passed in so edits and redisplayed
 * failed submits validate on load, not just on the next keystroke.
 */
export default function releaseDate({ year = '', month = '', day = '' } = {}) {
  return {
    year,
    month,
    day,

    get collectionYear() {
      const store = this.$store.collection;
      return store && store.year ? Number(store.year) : null;
    },

    get mismatch() {
      const y = this.year ? Number(this.year) : null;
      return y !== null && this.collectionYear !== null && y !== this.collectionYear;
    },

    get dateError() {
      const y = this.year ? Number(this.year) : null;
      const m = this.month ? Number(this.month) : null;
      const d = this.day ? Number(this.day) : null;

      if (m !== null && (m < 1 || m > 12)) return 'Month must be between 1 and 12.';
      if (d !== null && (d < 1 || d > 31)) return 'Day must be between 1 and 31.';
      if (d !== null && m === null) return 'Add a month before a day.';
      if (m !== null && d !== null) {
        // No year yet → check against a leap year so a bare "29 Feb" is allowed.
        const probe = new Date(y || 2000, m - 1, d);
        if (probe.getMonth() !== m - 1 || probe.getDate() !== d) {
          return 'That’s not a real date.';
        }
      }
      return '';
    },
  };
}

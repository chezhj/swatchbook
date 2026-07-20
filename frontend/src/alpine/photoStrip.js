/**
 * Dot indicators for the detail page's photo carousel — one dot per photo, the
 * active one tracking the scroll position, tap a dot to jump. The strip itself
 * stays plain CSS scroll-snap; this only observes it.
 */
export default function photoStrip(count = 0) {
  return {
    count,
    active: 0,

    // The snap position of photo i: centred in the strip, as scroll-snap-align
    // will place it. Derived from the element rather than index * width so the
    // dots and the browser's snapping never disagree (the last photo's snap
    // position is clamped to the end of the scroll range, not on the grid).
    snapLeft(index) {
      const el = this.$refs.strip;
      const img = el.querySelectorAll('img')[index];
      if (!img) return 0;
      const target = img.offsetLeft - (el.clientWidth - img.clientWidth) / 2;
      return Math.max(0, Math.min(el.scrollWidth - el.clientWidth, target));
    },

    onScroll() {
      const left = this.$refs.strip.scrollLeft;
      let nearest = 0;
      for (let i = 1; i < this.count; i += 1) {
        if (Math.abs(this.snapLeft(i) - left) < Math.abs(this.snapLeft(nearest) - left)) {
          nearest = i;
        }
      }
      this.active = nearest;
    },

    // Instant jump, deliberately: smooth scrolling fights mandatory snapping (the
    // animation gets cancelled and the strip re-snaps to the wrong photo), and
    // instant is what prefers-reduced-motion would ask for anyway.
    goTo(index) {
      this.$refs.strip.scrollTo({ left: this.snapLeft(index) });
      this.active = index;
    },
  };
}

import Alpine from 'alpinejs';

import './styles/main.scss';

import collectionCombo from './alpine/collectionCombo.js';
import collectionGrid from './alpine/grid.js';
import compareSelection from './alpine/compare.js';
import logEntryForm from './alpine/logForm.js';
import logList from './alpine/logList.js';
import photoSlots from './alpine/photoSlots.js';
import photoStrip from './alpine/photoStrip.js';
import photoTile from './alpine/photoTile.js';
import polishSelect from './alpine/polishSelect.js';
import releaseDate from './alpine/releaseDate.js';

// Shared between collectionCombo (writer) and releaseDate (reader) on the polish form,
// so the release-year field can warn live when it disagrees with the chosen collection.
Alpine.store('collection', { year: null });

Alpine.data('collectionCombo', collectionCombo);
Alpine.data('collectionGrid', collectionGrid);
Alpine.data('compareSelection', compareSelection);
Alpine.data('logEntryForm', logEntryForm);
Alpine.data('logList', logList);
Alpine.data('photoSlots', photoSlots);
Alpine.data('photoStrip', photoStrip);
Alpine.data('photoTile', photoTile);
Alpine.data('polishSelect', polishSelect);
Alpine.data('releaseDate', releaseDate);

window.Alpine = Alpine;
Alpine.start();

// Register the service worker (web/templates/web/sw.js, served at /sw.js). Only from a
// real build — under `npm run dev` import.meta.env.DEV is true and a caching SW would
// just fight Vite's HMR. sw.js itself lives at the root so its scope is the whole app.
if ('serviceWorker' in navigator && !import.meta.env.DEV) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((err) => {
      console.error('Service worker registration failed:', err);
    });
  });
}

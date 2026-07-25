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

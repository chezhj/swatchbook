import Alpine from 'alpinejs';

import './styles/main.scss';

import collectionCombo from './alpine/collectionCombo.js';
import collectionGrid from './alpine/grid.js';
import compareSelection from './alpine/compare.js';
import logEntryForm from './alpine/logForm.js';
import logList from './alpine/logList.js';
import photoStrip from './alpine/photoStrip.js';
import photoTile from './alpine/photoTile.js';
import polishSelect from './alpine/polishSelect.js';

Alpine.data('collectionCombo', collectionCombo);
Alpine.data('collectionGrid', collectionGrid);
Alpine.data('compareSelection', compareSelection);
Alpine.data('logEntryForm', logEntryForm);
Alpine.data('logList', logList);
Alpine.data('photoStrip', photoStrip);
Alpine.data('photoTile', photoTile);
Alpine.data('polishSelect', polishSelect);

window.Alpine = Alpine;
Alpine.start();

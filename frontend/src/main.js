import Alpine from 'alpinejs';

import './styles/main.scss';

import collectionGrid from './alpine/grid.js';
import compareSelection from './alpine/compare.js';
import logEntryForm from './alpine/logForm.js';
import logList from './alpine/logList.js';
import photoStrip from './alpine/photoStrip.js';
import photoTile from './alpine/photoTile.js';

Alpine.data('collectionGrid', collectionGrid);
Alpine.data('compareSelection', compareSelection);
Alpine.data('logEntryForm', logEntryForm);
Alpine.data('logList', logList);
Alpine.data('photoStrip', photoStrip);
Alpine.data('photoTile', photoTile);

window.Alpine = Alpine;
Alpine.start();

import Alpine from 'alpinejs';

import './styles/main.scss';

import collectionGrid from './alpine/grid.js';
import compareSelection from './alpine/compare.js';
import logEntryForm from './alpine/logForm.js';

Alpine.data('collectionGrid', collectionGrid);
Alpine.data('compareSelection', compareSelection);
Alpine.data('logEntryForm', logEntryForm);

window.Alpine = Alpine;
Alpine.start();

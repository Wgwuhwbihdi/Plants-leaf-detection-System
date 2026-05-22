// History filtering utilities for server-rendered history entries.
class HistoryFilter {
  constructor() {
    this.entries = Array.from(document.querySelectorAll('[data-history-entry]'));
    this.filters = {
      dateFrom: '',
      dateTo: '',
      disease: '',
      confidenceLevel: ''
    };
  }

  updateFilter(filterType, value) {
    if (!(filterType in this.filters)) return;
    this.filters[filterType] = (value || '').toString().trim();
    this.applyFilters();
  }

  applyFilters() {
    let visibleCount = 0;

    this.entries.forEach(entry => {
      const entryDate = (entry.dataset.timestamp || '').trim();
      const entryDisease = (entry.dataset.disease || '').toLowerCase();
      const entryConfidence = (entry.dataset.confidenceLevel || '').trim();
      const isBatch = entry.dataset.batch === 'true';

      let visible = true;

      if (this.filters.dateFrom && entryDate < this.filters.dateFrom) {
        visible = false;
      }

      if (this.filters.dateTo && entryDate > this.filters.dateTo) {
        visible = false;
      }

      if (this.filters.disease) {
        const diseaseQuery = this.filters.disease.toLowerCase();
        if (!entryDisease.includes(diseaseQuery)) {
          visible = false;
        }
      }

      if (this.filters.confidenceLevel) {
        if (isBatch) {
          // Batch cards represent mixed results; hide when a specific level is selected.
          visible = false;
        } else if (entryConfidence !== this.filters.confidenceLevel) {
          visible = false;
        }
      }

      entry.style.display = visible ? '' : 'none';
      if (visible) {
        visibleCount += 1;
      }
    });

    window.dispatchEvent(new CustomEvent('historyFiltered', {
      detail: {
        filtered: visibleCount,
        total: this.entries.length
      }
    }));
  }

  reset() {
    this.filters = {
      dateFrom: '',
      dateTo: '',
      disease: '',
      confidenceLevel: ''
    };
    this.applyFilters();
  }

  export(format = 'json') {
    const normalized = (format || 'json').toLowerCase();
    const exportFormat = normalized === 'csv' ? 'csv' : 'json';
    window.location.href = `/export/history?format=${encodeURIComponent(exportFormat)}`;
  }
}

const historyFilter = new HistoryFilter();

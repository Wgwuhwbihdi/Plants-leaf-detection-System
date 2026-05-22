/**
 * Phyto Lab - Main Frontend Application Logic
 * Encapsulated in an IIFE to avoid polluting the global namespace.
 */
(function () {
  const rootElement = document.documentElement;

  /**
   * Registers a service worker to enable offline capabilities and PWA features.
   */
  function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/static/sw.js')
        .then(() => {
          console.log('Service worker registered successfully.');
        })
        .catch(error => {
          console.warn('Service worker registration failed:', error);
        });
    }
  }

  /**
   * Initializes real-time filtering for the history page.
   * Allows users to filter their past scans by disease name, date range, and confidence level.
   */
  function setupHistoryFilters() {
    const filterFormElement = document.getElementById('history-filter-form');
    if (!filterFormElement) return;

    const historyEntries = Array.from(document.querySelectorAll('[data-history-entry]'));
    const diseaseFilterInput = document.getElementById('disease-filter');
    const dateFromFilterInput = document.getElementById('date-from-filter');
    const dateToFilterInput = document.getElementById('date-to-filter');
    const confidenceFilterInput = document.getElementById('confidence-filter');
    const clearFiltersButton = document.getElementById('clear-history-filters');

    // Helper function to standardize text for case-insensitive comparison
    function normalizeText(text) {
      return (text || '').toString().toLowerCase().trim();
    }

    /**
     * Applies the current filter values to all history entries on the page.
     */
    function applyFilters() {
      const searchedDiseaseName = normalizeText(diseaseFilterInput.value);
      const filterStartDate = dateFromFilterInput.value;
      const filterEndDate = dateToFilterInput.value;
      const requiredConfidence = confidenceFilterInput.value;

      historyEntries.forEach(entryElement => {
        let isEntryVisible = true;
        
        // Extract data attributes from the DOM element
        const entryTimestamp = entryElement.dataset.timestamp || '';
        const entryDiseaseName = normalizeText(entryElement.dataset.disease || '');
        const entryConfidenceLevel = entryElement.dataset.confidenceLevel || 'all';
        const isBatchEntry = entryElement.dataset.batch === 'true';

        // 1. Filter by Date Range
        if (filterStartDate && entryTimestamp < filterStartDate) isEntryVisible = false;
        if (filterEndDate && entryTimestamp > filterEndDate) isEntryVisible = false;

        // 2. Filter by Disease Name (Batch entries don't have a single disease name to filter by)
        if (searchedDiseaseName && !entryDiseaseName.includes(searchedDiseaseName)) {
          if (!isBatchEntry) isEntryVisible = false;
        }

        // 3. Filter by Confidence Level
        if (requiredConfidence !== 'all') {
          if (!isBatchEntry && entryConfidenceLevel !== requiredConfidence) isEntryVisible = false;
          // If the user wants a specific confidence, hide batch summaries as they represent multiple confidences
          if (isBatchEntry && requiredConfidence !== 'batch') isEntryVisible = false;
        }

        // Update DOM visibility
        entryElement.style.display = isEntryVisible ? '' : 'none';
      });
    }

    // Attach event listeners
    filterFormElement.addEventListener('input', applyFilters);
    
    clearFiltersButton.addEventListener('click', event => {
      event.preventDefault();
      // Reset all inputs
      diseaseFilterInput.value = '';
      dateFromFilterInput.value = '';
      dateToFilterInput.value = '';
      confidenceFilterInput.value = 'all';
      // Re-apply empty filters to show all entries
      applyFilters();
    });
  }

  /**
   * Initializes the modal image viewer for clicking to enlarge scan images.
   */
  function setupImageViewer() {
    const modalContainer = document.getElementById('image-viewer-modal');
    const modalImageElement = document.getElementById('image-viewer-img');
    const imageTriggers = Array.from(document.querySelectorAll('[data-image-viewer]'));
    const closeViewerButton = document.getElementById('close-image-viewer');
    const zoomInButton = document.getElementById('zoom-in');
    const zoomOutButton = document.getElementById('zoom-out');
    
    let currentZoomScale = 1;

    // Exit early if the viewer elements don't exist on this page
    if (!modalContainer || !modalImageElement || !imageTriggers.length) return;

    // Attach click listeners to all thumbnail images
    imageTriggers.forEach(triggerElement => {
      triggerElement.addEventListener('click', () => {
        modalImageElement.src = triggerElement.dataset.imageSrc;
        currentZoomScale = 1; // Reset zoom level
        modalImageElement.style.transform = 'scale(1)';
        modalContainer.classList.remove('hidden'); // Show modal
      });
    });

    if (closeViewerButton) {
      closeViewerButton.addEventListener('click', () => modalContainer.classList.add('hidden'));
    }

    // Handle zoom functionality
    if (zoomInButton) {
      zoomInButton.addEventListener('click', () => {
        currentZoomScale = Math.min(2.5, currentZoomScale + 0.25);
        modalImageElement.style.transform = `scale(${currentZoomScale})`;
      });
    }

    if (zoomOutButton) {
      zoomOutButton.addEventListener('click', () => {
        currentZoomScale = Math.max(1, currentZoomScale - 0.25);
        modalImageElement.style.transform = `scale(${currentZoomScale})`;
      });
    }

    // Close modal when clicking outside the image
    modalContainer.addEventListener('click', event => {
      if (event.target === modalContainer) modalContainer.classList.add('hidden');
    });
  }

  /**
   * Manages the PWA "Install App" prompt logic.
   */
  function setupInstallPrompt() {
    let deferredInstallEvent;
    const installAppButton = document.getElementById('install-app');
    if (!installAppButton) return;

    // Intercept the browser's default install prompt
    window.addEventListener('beforeinstallprompt', event => {
      event.preventDefault();
      deferredInstallEvent = event;
      installAppButton.classList.remove('hidden'); // Show our custom install button
    });

    installAppButton.addEventListener('click', async () => {
      if (!deferredInstallEvent) return;
      deferredInstallEvent.prompt();
      
      const userChoice = await deferredInstallEvent.userChoice;
      if (userChoice.outcome === 'accepted') {
        installAppButton.classList.add('hidden');
      }
      deferredInstallEvent = null; // Clear the saved event once used
    });
  }

  /**
   * Initializes the language selection dropdown to dynamically redirect the user.
   */
  function setupLanguageDropdown() {
    const languageSelectors = Array.from(document.querySelectorAll('[data-language-select]'));
    if (!languageSelectors.length) return;

    languageSelectors.forEach(selectorElement => {
      selectorElement.addEventListener('change', event => {
        const selectedLanguageCode = (event.target.value || '').trim();
        if (!selectedLanguageCode) return;
        
        // Redirect to the language setting endpoint
        window.location.href = `/set-language/${encodeURIComponent(selectedLanguageCode)}`;
      });
    });
  }

  // Initialize all frontend components when the DOM is fully loaded
  window.addEventListener('load', () => {
    registerServiceWorker();
    setupHistoryFilters();
    setupImageViewer();
    setupInstallPrompt();
    setupLanguageDropdown();
  });
})();

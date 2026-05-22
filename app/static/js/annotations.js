// Annotation and Zoom utilities
class AnnotationManager {
  constructor() {
    this.notes = this.loadNotes();
    this.initNoteHandlers();
  }

  loadNotes() {
    try {
      return JSON.parse(localStorage.getItem('phytoNotes')) || {};
    } catch {
      return {};
    }
  }

  saveNotes() {
    localStorage.setItem('phytoNotes', JSON.stringify(this.notes));
  }

  addNote(specimenId, noteText, timestamp = new Date().toISOString()) {
    if (!this.notes[specimenId]) {
      this.notes[specimenId] = [];
    }
    this.notes[specimenId].push({
      text: noteText,
      timestamp: timestamp,
      id: `note-${Date.now()}`
    });
    this.saveNotes();
    return this.notes[specimenId][this.notes[specimenId].length - 1];
  }

  deleteNote(specimenId, noteId) {
    if (this.notes[specimenId]) {
      this.notes[specimenId] = this.notes[specimenId].filter(n => n.id !== noteId);
      this.saveNotes();
    }
  }

  getNotes(specimenId) {
    return this.notes[specimenId] || [];
  }

  initNoteHandlers() {
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('note-delete-btn')) {
        const specimenId = e.target.dataset.specimenId;
        const noteId = e.target.dataset.noteId;
        this.deleteNote(specimenId, noteId);
        e.target.closest('.note-item').remove();
      }
    });
  }

  renderNotes(specimenId, containerSelector) {
    const container = document.querySelector(containerSelector);
    if (!container) return;

    const notes = this.getNotes(specimenId);
    const notesHtml = notes.map(note => `
      <div class="note-item bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 dark:border-yellow-700 rounded-lg p-3 mb-2">
        <div class="flex justify-between items-start gap-2">
          <div class="flex-1">
            <p class="text-sm text-on-surface dark:text-slate-200">${this.escapeHtml(note.text)}</p>
            <p class="text-xs text-on-surface-variant dark:text-slate-400 mt-1">
              ${new Date(note.timestamp).toLocaleString()}
            </p>
          </div>
          <button class="note-delete-btn text-red-600 hover:text-red-700 material-symbols-outlined text-sm" 
                  data-specimen-id="${specimenId}" 
                  data-note-id="${note.id}">
            close
          </button>
        </div>
      </div>
    `).join('');

    container.innerHTML = notesHtml || '<p class="text-sm text-on-surface-variant">No notes yet</p>';
  }

  escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
  }
}

// Image Zoom utilities
class ImageZoom {
  constructor(imgSelector) {
    this.img = document.querySelector(imgSelector);
    if (!this.img) return;
    this.setupZoom();
  }

  setupZoom() {
    const container = document.createElement('div');
    container.classList.add('zoom-container');
    container.style.cssText = `
      position: relative;
      display: inline-block;
      cursor: zoom-in;
      overflow: hidden;
      border-radius: 12px;
    `;

    this.img.parentNode.insertBefore(container, this.img);
    container.appendChild(this.img);

    const zoomModal = this.createZoomModal();
    document.body.appendChild(zoomModal);

    container.addEventListener('click', () => this.openZoom());
  }

  createZoomModal() {
    const modal = document.createElement('div');
    modal.id = 'zoom-modal';
    modal.style.cssText = `
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.8);
      z-index: 9999;
      overflow: auto;
    `;

    const content = document.createElement('div');
    content.style.cssText = `
      position: relative;
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
    `;

    const imgZoomed = this.img.cloneNode();
    imgZoomed.style.cssText = `
      max-width: 90vw;
      max-height: 90vh;
      object-fit: contain;
      cursor: zoom-out;
    `;

    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '✕';
    closeBtn.style.cssText = `
      position: absolute;
      top: 20px;
      right: 30px;
      font-size: 28px;
      background: none;
      border: none;
      color: white;
      cursor: pointer;
      z-index: 10000;
    `;

    content.appendChild(imgZoomed);
    content.appendChild(closeBtn);
    modal.appendChild(content);

    const closeZoom = () => modal.style.display = 'none';
    closeBtn.addEventListener('click', closeZoom);
    imgZoomed.addEventListener('click', closeZoom);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeZoom();
    });

    this.zoomModal = modal;
    this.zoomedImg = imgZoomed;

    return modal;
  }

  openZoom() {
    this.zoomModal.style.display = 'block';
    document.body.style.overflow = 'hidden';
  }

  closeZoom() {
    this.zoomModal.style.display = 'none';
    document.body.style.overflow = 'auto';
  }
}

// Initialize global managers
const annotationManager = new AnnotationManager();

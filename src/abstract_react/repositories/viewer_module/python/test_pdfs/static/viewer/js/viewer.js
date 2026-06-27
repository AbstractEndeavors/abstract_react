import { PDFViewer } from './pdfViewer.js';

document.addEventListener('DOMContentLoaded', () => {
  const roots = document.querySelectorAll('.viewer-root');

  roots.forEach(root => {
    const raw = root.dataset.config;
    if (!raw) return;

    let data;
    try {
      data = JSON.parse(raw);
    } catch (e) {
      console.error("Invalid viewer config:", e);
      return;
    }

    const viewer = new PDFViewer(root, data);
    viewer.init();
  });
});

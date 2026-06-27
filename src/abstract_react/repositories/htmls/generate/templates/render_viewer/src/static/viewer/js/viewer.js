import { PDFViewer } from './pdfViewer.js';

document.addEventListener('DOMContentLoaded', () => {
  const roots = document.querySelectorAll('.viewer-root');

  roots.forEach(root => {
    const data = window.__VIEWER_DATA__;
    if (!data) return;

    const viewer = new PDFViewer(root, data);
    viewer.init();
  });
});

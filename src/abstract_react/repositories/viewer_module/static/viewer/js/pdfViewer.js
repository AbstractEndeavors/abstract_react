export class PDFViewer {
  constructor(root, config) {
    this.root = root;
    this.pages = config.pages || [];
    this.pdfUrl = config.pdfUrl || null;
    this.total = config.total || this.pages.length;
    this.keywords = config.keywords || [];

    this.cur = 1;
    this.format = 'pdf';
    this.refs = {};
  }

  init() {
    this.bindRefs();
    this.bindEvents();
    this.goPage(1);
  }

  bindRefs() {
    const q = (sel) => this.root.querySelector(sel);

    this.refs = {
      content: q('[data-role="content"]'),
      pageDisplay: q('[data-role="page-display"]'),
      formatBtns: this.root.querySelectorAll('[data-format]')
    };
  }

  bindEvents() {
    this.refs.formatBtns.forEach(btn => {
      btn.addEventListener('click', () => this.setFormat(btn.dataset.format));
    });

    this.root.addEventListener('click', (e) => {
      const nav = e.target.dataset.nav;

      if (nav === 'next') this.goPage(this.cur + 1);
      if (nav === 'prev') this.goPage(this.cur - 1);
      if (nav === 'first') this.goPage(1);
      if (nav === 'last') this.goPage(this.total);
    });
  }

  setFormat(fmt) {
    this.format = fmt;
    this.renderContent();
  }

  goPage(n) {
    this.cur = Math.max(1, Math.min(this.total, n));

    if (this.refs.pageDisplay) {
      this.refs.pageDisplay.textContent = `Page ${this.cur} / ${this.total}`;
    }

    this.renderContent();
  }

  renderContent() {
    const area = this.refs.content;

    if (!area) return;

    if (this.format === 'pdf') {
      area.innerHTML = this.pdfUrl
        ? `<iframe src="${this.pdfUrl}#page=${this.cur}" style="width:100%;height:100%"></iframe>`
        : `<p>No PDF available</p>`;
    }
  }
}

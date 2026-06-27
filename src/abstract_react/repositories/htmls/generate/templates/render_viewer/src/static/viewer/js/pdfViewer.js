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
    this.renderKeywords();
    this.bindEvents();
    this.buildThumbs();
    this.goPage(1);
  }

  bindRefs() {
    const q = (sel) => this.root.querySelector(sel);

    this.refs = {
      thumbs: q('[data-role="thumbs"]'),
      content: q('[data-role="content"]'),
      pageDisplay: q('[data-role="page-display"]'),
      searchInput: q('[data-role="search"]'),
      searchStatus: q('[data-role="search-status"]'),
      formatBtns: this.root.querySelectorAll('[data-format]'),
      keywords: q('[data-role="keywords"]')
    };
  }

  bindEvents() {
    this.refs.searchInput?.addEventListener('input', this.debounce((e) => {
      this.runSearch(e.target.value.trim());
    }, 250));

    this.refs.formatBtns.forEach(btn => {
      btn.addEventListener('click', () => this.setFormat(btn.dataset.format));
    });

    this.root.addEventListener('click', (e) => {
      if (e.target.dataset.nav === 'next') this.goPage(this.cur + 1);
      if (e.target.dataset.nav === 'prev') this.goPage(this.cur - 1);
    });
  }

  renderKeywords() {
    if (!this.refs.keywords) return;
    this.refs.keywords.innerHTML = this.keywords.map(k =>
      `<span class="tag">${k}</span>`
    ).join('');
  }

  buildThumbs() {
    if (!this.refs.thumbs) return;

    this.refs.thumbs.innerHTML = this.pages.map(p => `
      <div class="thumb-item ${p.n===1?'active':''}" data-page="${p.n}">
        ${p.thumb
          ? `<img src="${p.thumb}" alt="${p.alt}" loading="lazy">`
          : `<div class="thumb-placeholder">p${p.n}</div>`}
      </div>
    `).join('');

    this.refs.thumbs.querySelectorAll('[data-page]').forEach(el => {
      el.addEventListener('click', () => this.goPage(Number(el.dataset.page)));
    });
  }

  goPage(n) {
    this.cur = Math.max(1, Math.min(this.total, n));
    this.updateUI();
    this.renderContent();
  }

  updateUI() {
    if (this.refs.pageDisplay) {
      this.refs.pageDisplay.textContent = `Page ${this.cur} / ${this.total}`;
    }

    this.refs.thumbs?.querySelectorAll('.thumb-item').forEach(el =>
      el.classList.toggle('active', Number(el.dataset.page) === this.cur)
    );
  }

  setFormat(fmt) {
    this.format = fmt;

    this.refs.formatBtns.forEach(btn =>
      btn.classList.toggle('active', btn.dataset.format === fmt)
    );

    this.renderContent();
  }

  renderContent() {
    const page = this.pages[this.cur - 1];
    const area = this.refs.content;

    if (!area) return;

    if (this.format === 'pdf') {
      area.innerHTML = this.pdfUrl
        ? `<iframe src="${this.pdfUrl}#page=${this.cur}" class="pdf-frame"></iframe>`
        : `<p>No PDF available</p>`;
    }

    if (this.format === 'images') {
      area.innerHTML = page?.thumb
        ? `<img src="${page.thumb}" class="img-view">`
        : `<p>No image</p>`;
    }

    if (this.format === 'text') {
      const text = page?.text || '(no text)';
      const q = this.refs.searchInput?.value || '';
      area.innerHTML = this.highlight(text, q);
    }
  }

  runSearch(q) {
    if (!q) return this.renderContent();

    this.setFormat('text');

    const hits = this.pages
      .map(p => ({
        page: p.n,
        text: p.text || ''
      }))
      .filter(p => p.text.toLowerCase().includes(q.toLowerCase()));

    if (!hits.length) {
      this.refs.content.innerHTML = `<p>No results</p>`;
      return;
    }

    this.refs.content.innerHTML = hits.map(h => `
      <div class="hit" data-page="${h.page}">
        <strong>Page ${h.page}</strong>
        <p>${this.highlightSnippet(h.text, q)}</p>
      </div>
    `).join('');

    this.refs.content.querySelectorAll('[data-page]').forEach(el => {
      el.addEventListener('click', () => {
        this.goPage(Number(el.dataset.page));
        this.setFormat('text');
      });
    });
  }

  highlight(text, q) {
    if (!q) return `<pre>${this.escape(text)}</pre>`;
    const rx = new RegExp(`(${this.escapeRegex(q)})`, 'gi');
    return `<pre>${this.escape(text).replace(rx, '<mark>$1</mark>')}</pre>`;
  }

  highlightSnippet(text, q) {
    const idx = text.toLowerCase().indexOf(q.toLowerCase());
    const start = Math.max(0, idx - 50);
    const end = Math.min(text.length, idx + 50);
    return this.highlight(text.slice(start, end), q);
  }

  escape(s) {
    return s.replace(/[&<>"']/g, m => ({
      '&':'&amp;',
      '<':'&lt;',
      '>':'&gt;',
      '"':'&quot;',
      "'":'&#39;'
    }[m]));
  }

  escapeRegex(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  debounce(fn, ms) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  }
}

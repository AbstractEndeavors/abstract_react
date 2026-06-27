  <script>
    (() => {
      const cfg = window.__VIEWER_CONFIG__ || {};
      const pages = Array.isArray(cfg.pages) ? cfg.pages : [];
      const total = Number(cfg.total || pages.length || 1);

      let cur = 1;
      let mode = "images";
      let matches = [];
      let matchIndex = -1;
      let observer = null;
      let suppressObserver = false;

      const viewerScroll = document.getElementById("viewer-scroll");
      const thumbs = document.getElementById("thumbs");
      const pageDisplay = document.getElementById("page-display");
      const searchInput = document.getElementById("search-input");
      const searchStatus = document.getElementById("search-status");

      const btnImages = document.getElementById("btn-images");
      const btnText = document.getElementById("btn-text");
      const btnPdf = document.getElementById("btn-pdf");
      const btnFirst = document.getElementById("btn-first");
      const btnPrev = document.getElementById("btn-prev");
      const btnNext = document.getElementById("btn-next");
      const btnLast = document.getElementById("btn-last");

      document.getElementById("doc-title").textContent = cfg.title || "PDF Viewer";
      document.getElementById("doc-desc").textContent = cfg.description || "";

      const chipWrap = document.getElementById("keyword-chips");
      (cfg.keywords || []).forEach((kw) => {
        const span = document.createElement("span");
        span.className = "chip";
        span.textContent = kw;
        chipWrap.appendChild(span);
      });

      function escapeHtml(value) {
        return String(value)
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;")
          .replace(/'/g, "&#39;");
      }

      function pageAt(n) {
        return pages[Math.max(0, Math.min(total - 1, n - 1))] || pages[0] || {};
      }

      function getCardId(pageNum) {
        return `page-card-${pageNum}`;
      }

      function normalizeKeywords(page) {
        const raw = page.page_keywords || [];
        if (Array.isArray(raw)) return raw.filter(Boolean);
        if (typeof raw === "string") return raw.split(",").map(v => v.trim()).filter(Boolean);
        return [];
      }

      function highlightText(text, term) {
        const safe = escapeHtml(text || "");
        if (!term) return safe;
        const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        return safe.replace(new RegExp(`(${escaped})`, "ig"), "<mark>$1</mark>");
      }

      function renderThumbs() {
        thumbs.innerHTML = "";
        pages.forEach((page) => {
          const button = document.createElement("button");
          button.type = "button";
          button.className = "thumb" + (page.n === cur ? " active" : "");
          button.onclick = () => goPage(page.n, { focusMode: true });

          const img = page.thumb
            ? `<img src="${page.thumb}" alt="${escapeHtml(page.alt || "")}" loading="lazy" />`
            : `<img alt="" />`;

          button.innerHTML = `
            ${img}
            <div class="thumb-meta">
              <div class="thumb-page">Page ${page.n}</div>
              <div class="thumb-title">${escapeHtml(page.page_title || "")}</div>
            </div>
          `;
          thumbs.appendChild(button);
        });
      }

      function buildImageCards() {
        const cards = pages.map((page) => {
          const keywords = normalizeKeywords(page).slice(0, 8).join(", ");
          return `
            <section class="page-card ${page.n === cur ? "active" : ""}" id="${getCardId(page.n)}" data-page="${page.n}">
              <div class="page-head">
                <div class="page-head-left">
                  <div class="page-number">Page ${page.n}</div>
                  <div class="page-scope">${escapeHtml(page.page_title || "")}</div>
                </div>
                <div class="page-keywords">${escapeHtml(keywords)}</div>
              </div>
              <div class="page-image-wrap">
                ${
                  page.image
                    ? `<img class="page-image" src="${page.image}" alt="${escapeHtml(page.alt || "")}" loading="lazy" />`
                    : `<div class="page-text">No page image found.</div>`
                }
              </div>
            </section>
          `;
        }).join("");

        viewerScroll.innerHTML = `<div class="doc-stack">${cards}</div>`;
      }

      function buildTextCards() {
        const term = searchInput.value.trim();
        const cards = pages.map((page) => {
          const keywords = normalizeKeywords(page).slice(0, 8).join(", ");
          return `
            <section class="page-card ${page.n === cur ? "active" : ""}" id="${getCardId(page.n)}" data-page="${page.n}">
              <div class="page-head">
                <div class="page-head-left">
                  <div class="page-number">Page ${page.n}</div>
                  <div class="page-scope">${escapeHtml(page.page_title || "")}</div>
                </div>
                <div class="page-keywords">${escapeHtml(keywords)}</div>
              </div>
              <div class="page-text-wrap">
                <div class="page-text">${highlightText(page.text || "No OCR text available.", term)}</div>
              </div>
            </section>
          `;
        }).join("");

        viewerScroll.innerHTML = `<div class="doc-stack">${cards}</div>`;
      }

      function buildPdfView() {
        viewerScroll.innerHTML = `
          <div class="pdf-single">
            <iframe
              class="pdf-frame"
              src="${cfg.pdfUrl}#page=${cur}"
              title="${escapeHtml(cfg.title || "PDF")}"
              loading="lazy">
            </iframe>
          </div>
        `;
      }

      function activateCurrentCard() {
        document.querySelectorAll(".page-card").forEach((card) => {
          const pageNum = Number(card.dataset.page || 0);
          card.classList.toggle("active", pageNum === cur);
        });
      }

      function updateToolbar() {
        pageDisplay.textContent = `Page ${cur} / ${total}`;
        btnImages.classList.toggle("active", mode === "images");
        btnText.classList.toggle("active", mode === "text");
        btnPdf.classList.toggle("active", mode === "pdf");
      }

      function teardownObserver() {
        if (observer) {
          observer.disconnect();
          observer = null;
        }
      }

      function setupObserver() {
        teardownObserver();

        if (mode === "pdf") return;

        const cards = Array.from(document.querySelectorAll(".page-card"));
        if (!cards.length) return;

        observer = new IntersectionObserver((entries) => {
          if (suppressObserver) return;

          let best = null;
          for (const entry of entries) {
            if (!entry.isIntersecting) continue;
            if (!best || entry.intersectionRatio > best.intersectionRatio) {
              best = entry;
            }
          }

          if (!best) return;

          const pageNum = Number(best.target.dataset.page || cur);
          if (pageNum !== cur) {
            cur = pageNum;
            renderThumbs();
            activateCurrentCard();
            updateToolbar();
          }
        }, {
          root: viewerScroll,
          threshold: [0.25, 0.5, 0.75, 1],
        });

        cards.forEach((card) => observer.observe(card));
      }

      function scrollToCurrentPage() {
        if (mode === "pdf") return;
        const card = document.getElementById(getCardId(cur));
        if (!card) return;

        suppressObserver = true;
        card.scrollIntoView({ behavior: "smooth", block: "start" });
        activateCurrentCard();
        renderThumbs();
        updateToolbar();

        window.setTimeout(() => {
          suppressObserver = false;
        }, 450);
      }

      function renderMode() {
        if (mode === "images") {
          buildImageCards();
        } else if (mode === "text") {
          buildTextCards();
        } else {
          buildPdfView();
        }

        renderThumbs();
        updateToolbar();
        setupObserver();

        if (mode !== "pdf") {
          window.requestAnimationFrame(() => {
            scrollToCurrentPage();
          });
        }
      }

      function goPage(n, options = {}) {
        cur = Math.max(1, Math.min(total, n));

        if (mode === "pdf") {
          buildPdfView();
          updateToolbar();
          renderThumbs();
          return;
        }

        renderThumbs();
        activateCurrentCard();
        updateToolbar();

        if (options.focusMode !== false) {
          scrollToCurrentPage();
        }
      }

      function setMode(nextMode) {
        mode = nextMode;
        renderMode();
      }

      function buildMatches(term) {
        matches = [];
        matchIndex = -1;

        if (!term) {
          searchStatus.textContent = "";
          if (mode === "text") {
            renderMode();
          }
          return;
        }

        const lower = term.toLowerCase();
        pages.forEach((page) => {
          const text = String(page.text || "").toLowerCase();
          if (text.includes(lower)) matches.push(page.n);
        });

        if (!matches.length) {
          searchStatus.textContent = "No matches";
          if (mode === "text") {
            renderMode();
          }
          return;
        }

        searchStatus.textContent = `${matches.length} matching page${matches.length === 1 ? "" : "s"}`;
        matchIndex = 0;
        mode = "text";
        renderMode();
        goPage(matches[0], { focusMode: true });
      }

      btnImages.onclick = () => setMode("images");
      btnText.onclick = () => setMode("text");
      btnPdf.onclick = () => setMode("pdf");

      btnFirst.onclick = () => goPage(1);
      btnPrev.onclick = () => goPage(cur - 1);
      btnNext.onclick = () => goPage(cur + 1);
      btnLast.onclick = () => goPage(total);

      searchInput.addEventListener("input", () => buildMatches(searchInput.value.trim()));

      document.addEventListener("keydown", (event) => {
        if (event.key === "ArrowLeft") goPage(cur - 1);
        if (event.key === "ArrowRight") goPage(cur + 1);

        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "f") {
          event.preventDefault();
          searchInput.focus();
          searchInput.select();
        }

        if (event.key === "Enter" && document.activeElement === searchInput && matches.length) {
          matchIndex = (matchIndex + 1) % matches.length;
          goPage(matches[matchIndex], { focusMode: true });
        }
      });

      renderMode();
    })();
  </script>

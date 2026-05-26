/* ══════════════════════════════════════
   TSHOP — script.js
   ══════════════════════════════════════ */

// ── Live Search ──────────────────────────────
const searchInput    = document.getElementById('searchInput');
const searchDropdown = document.getElementById('searchDropdown');
let searchTimer;

if (searchInput) {
  searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    const q = searchInput.value.trim();
    if (q.length < 2) { closeDropdown(); return; }
    searchTimer = setTimeout(() => fetchSuggestions(q), 280);
  });

  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); doSearch(); }
    if (e.key === 'Escape') closeDropdown();
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('#searchWrap')) closeDropdown();
  });
}

async function fetchSuggestions(q) {
  try {
    const res  = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    renderDropdown(data);
  } catch (err) {
    console.warn('Search error:', err);
  }
}

function renderDropdown(items) {
  if (!items.length) { closeDropdown(); return; }
  searchDropdown.innerHTML = items.map(item => `
    <div class="search-dd-item" onclick="goToProduct(${item.id})">
      <img src="${item.image_url}" alt="${item.name}"
           onerror="this.src='https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=80'" />
      <div>
        <div class="dd-name">${item.name}</div>
        <div class="dd-price">R$ ${formatPrice(item.price)}</div>
      </div>
    </div>
  `).join('');
  searchDropdown.classList.add('open');
}

function closeDropdown() {
  if (searchDropdown) {
    searchDropdown.classList.remove('open');
    searchDropdown.innerHTML = '';
  }
}

function goToProduct(id) {
  window.location.href = `/produto/${id}`;
}

function doSearch() {
  const q = (searchInput?.value || '').trim();
  if (q) window.location.href = `/produtos?q=${encodeURIComponent(q)}`;
}

function doMobileSearch() {
  const inp = document.getElementById('mobileSearchInput');
  const q   = (inp?.value || '').trim();
  if (q) window.location.href = `/produtos?q=${encodeURIComponent(q)}`;
}

function formatPrice(n) {
  return Number(n).toFixed(2).replace('.', ',');
}

// ── Mobile Menu ──────────────────────────────
function toggleMenu() {
  const menu = document.getElementById('mobileMenu');
  if (menu) menu.classList.toggle('open');
}

// ── Scroll animations ───────────────────────
function initScrollReveal() {
  const cards = document.querySelectorAll('.product-card, .category-card, .trust-item, .admin-stat-card');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        entry.target.style.animationDelay = `${i * 40}ms`;
        entry.target.classList.add('revealed');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08 });

  cards.forEach(c => {
    c.style.opacity = '0';
    c.style.transform = 'translateY(18px)';
    c.style.transition = 'opacity .4s ease, transform .4s ease';
    observer.observe(c);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initScrollReveal();
});

// Reveal class triggered by observer
const style = document.createElement('style');
style.textContent = `.revealed { opacity: 1 !important; transform: none !important; }`;
document.head.appendChild(style);

// ── Admin: image preview ──────────────────────
const imgInput = document.querySelector('input[name="image_url"]');
if (imgInput) {
  imgInput.addEventListener('input', () => {
    let preview = document.getElementById('img-preview');
    if (!preview) {
      preview = document.createElement('img');
      preview.id = 'img-preview';
      preview.style.cssText = 'width:80px;height:80px;object-fit:cover;border-radius:8px;margin-top:.4rem;display:block;';
      imgInput.parentNode.appendChild(preview);
    }
    preview.src = imgInput.value;
    preview.onerror = () => { preview.style.display = 'none'; };
    preview.onload  = () => { preview.style.display = 'block'; };
  });
}

// ── Smooth scroll for anchor links ───────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', (e) => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth' }); }
  });
});

// ── Toast notifications ───────────────────────
function showToast(msg, type = 'info') {
  const toast = document.createElement('div');
  toast.textContent = msg;
  toast.style.cssText = `
    position:fixed; bottom:1.5rem; right:1.5rem; z-index:9999;
    background:${type === 'success' ? '#00e676' : '#00d4ff'};
    color:#000; padding:.7rem 1.4rem; border-radius:50px;
    font-weight:700; font-size:.85rem; font-family:'DM Sans',sans-serif;
    box-shadow:0 4px 20px rgba(0,0,0,.4);
    animation:fadeInUp .3s ease;
  `;
  document.body.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity .3s'; }, 2500);
  setTimeout(() => toast.remove(), 2900);
}

// Flash success after admin form submit
if (window.location.pathname === '/admin' && document.referrer.includes('/admin')) {
  showToast('✅ Produto adicionado com sucesso!', 'success');
}

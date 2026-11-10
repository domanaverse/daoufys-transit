// Menu mobile
const burger = document.getElementById('burger');
const navLinks = document.getElementById('navLinks');
burger.addEventListener('click', () => navLinks.classList.toggle('open'));
document.querySelectorAll('#navLinks a').forEach(a =>
  a.addEventListener('click', () => navLinks.classList.remove('open'))
);

// Header shadow on scroll
const header = document.getElementById('header');
window.addEventListener('scroll', () => {
  header.style.boxShadow = window.scrollY > 10 ? '0 4px 20px rgba(0,0,0,.12)' : '0 2px 14px rgba(0,0,0,.07)';
});

// Active nav on scroll
const sections = ['accueil','services','moyens','temoignages','contact'];
window.addEventListener('scroll', () => {
  let cur = 'accueil';
  sections.forEach(id => {
    const el = document.getElementById(id);
    if (el && window.scrollY >= el.offsetTop - 160) cur = id;
  });
  document.querySelectorAll('.nav-links > a').forEach(a => {
    a.classList.toggle('active', a.getAttribute('href') === '#' + cur);
  });
});

// Formulaire devis -> WhatsApp + message succès
document.getElementById('quoteForm').addEventListener('submit', e => {
  e.preventDefault();
  const nom = document.getElementById('qNom').value.trim();
  const tel = document.getElementById('qTel').value.trim();
  const email = document.getElementById('qEmail').value.trim();
  const service = document.getElementById('qService').value;
  const ville = document.getElementById('qVille').value;
  const msg = document.getElementById('qMsg').value.trim();
  if (!nom || !tel || !email || !service) { alert('Merci de remplir les champs obligatoires *.'); return; }
  const text = `Bonjour Daoufys Transit,%0AJe suis ${encodeURIComponent(nom)} (${encodeURIComponent(tel)} / ${encodeURIComponent(email)}).%0AService: ${encodeURIComponent(service)}%0AAgence: ${encodeURIComponent(ville)}%0ADétail: ${encodeURIComponent(msg)}`;
  window.open(`https://wa.me/212528292533?text=${text}`, '_blank');
  document.getElementById('quoteForm').classList.add('hidden');
  document.getElementById('quoteSuccess').classList.remove('hidden');
});

// Newsletter
document.getElementById('newsForm').addEventListener('submit', e => {
  e.preventDefault();
  e.target.classList.add('hidden');
  document.getElementById('newsOk').classList.remove('hidden');
});

// Hero vidéo : respect du mode réduit d'animation + reprise lecture
(function () {
  const v = document.querySelector('.hero-video');
  if (!v) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { v.pause(); return; }
  const p = v.play();
  if (p && p.catch) p.catch(() => {});
})();
 // Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const t = document.querySelector(a.getAttribute('href'));
    if (t) { e.preventDefault(); t.scrollIntoView({ behavior: 'smooth' }); }
  });
});

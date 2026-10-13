# Daoufys Transit — Site web

Site vitrine du transitaire agréé N°1426 (Agadir / Casablanca / Dakhla).
Déployé sur **GitHub Pages**.

## Pages
- `index.html` — Accueil + devis
- `transitaire-agree.html`, `transport.html`, `logistique.html`, `import-export.html`, `consulting.html`
- `moyens.html`, `partenaires.html`, `societe.html`, `contact.html`

## Déploiement GitHub Pages
1. Créer un repo sur github.com (ex : `daoufys-transit`)
2. Pousser ce dossier :
```bash
cd daoufys-transit
git init
git add .
git commit -m "Site Daoufys Transit"
git branch -M main
git remote add origin https://github.com/VOTRE-USER/daoufys-transit.git
git push -u origin main
```
3. Sur GitHub : Settings → Pages → Deploy from branch → `main` / `/ (root)` → Save
4. URL : `https://VOTRE-USER.github.io/daoufys-transit/`

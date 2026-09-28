# Luha Nihaz — Architectural Design Portfolio

Static portfolio site (HTML, CSS, vanilla JS) for Fathimath Luha Nihaz.

**Live:** https://seven-leven.github.io/Luha/

```
index.html                 Home: cover, semester contents, featured work
about.html                 About me: academics, experience, skills
cv.html                    CV page (prints to A4); PDF copy in assets/cv/
projects/                  One page per semester (4–6 are "coming soon")
css/style.css              Shared styles; semester colours set via <body data-sem="n">
js/main.js                 Menu, scroll reveals, image lightbox
assets/img/                Images cropped from the portfolio PDF
tools/extract_images.py    Re-crops images from source/SEM 123 low res.pdf (needs PyMuPDF + Pillow)
```

To add a new semester, copy a project page, set `data-sem`, and replace its images and text.
Preview locally by opening `index.html`, or run `python -m http.server`.

## Updating the CV PDF

With a local server running (`python -m http.server 5173`), print `cv.html` to PDF:

```
msedge --headless --no-pdf-header-footer --print-to-pdf=assets/cv/Luha-Nihaz-CV.pdf http://localhost:5173/cv.html
```

## Deploying

GitHub Pages serves the `main` branch root, so pushing to `main` updates the live site.

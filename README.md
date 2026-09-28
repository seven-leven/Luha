# Luha Nihaz — Architectural Design Portfolio

Static portfolio site (HTML, CSS, vanilla JS) for Fathimath Luha Nihaz.

```
index.html                 Home: cover, semester contents, featured work
about.html                 About me: academics, experience, skills
projects/                  One page per semester (4–6 are "coming soon")
css/style.css              Shared styles; semester colours set via <body data-sem="n">
js/main.js                 Menu, scroll reveals, image lightbox
assets/img/                Images cropped from the portfolio PDF
tools/extract_images.py    Re-crops images from "SEM 123 low res.pdf" (needs PyMuPDF + Pillow)
```

To add a new semester, copy a project page, set `data-sem`, and replace its images and text.
Preview locally by opening `index.html`, or run `python -m http.server`.

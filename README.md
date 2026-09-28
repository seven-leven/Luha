# Luha Nihaz — Architectural Design Portfolio

Static portfolio site (HTML, CSS, vanilla JS) for Fathimath Luha Nihaz.

**Live:** https://seven-leven.github.io/Luha/

## Preview locally

Double-click **`serve.bat`**, or run:

```
python build.py && python -m http.server 8000
```

then open http://localhost:8000.

## How it's built

The HTML pages are **generated**. Edit the files in `src/`, then run `python build.py`
(standard library only, nothing to install). The build also checks every link and image.

```
src/content/cv.json          Name, bio, contact, education, experience, skills
                             (feeds the home About block, about.html and cv.html)
src/content/semesters/N.json One file per semester: text, images, page sections
src/templates/layout.html    Shared <head>, header, nav and footer for every page
build.py                     Generates the pages below; --pdf also rebuilds the CV PDF

index.html, about.html, cv.html, projects/*.html   <- generated, don't edit by hand
css/style.css, css/cv.css    Styles; semester colours come from <body data-sem="n">
js/main.js                   Menu, scroll reveals, image lightbox
assets/img/                  Images (sem1/, sem2/, ... per semester)
assets/cv/Luha-Nihaz-CV.pdf  Downloadable CV
tools/extract_images.py      Re-crops images from source/SEM 123 low res.pdf (needs PyMuPDF + Pillow)
```

## Adding a semester

1. Put the images in `assets/img/semN/`.
2. In `src/content/semesters/N.json`, change `"status": "soon"` to `"complete"` and fill in the
   fields. Copy `3.json` as a starting point: it uses every section block type
   (`figure`, `cards`, `statement`, `steps`, `grid`, `split`, `gallery`).
3. Run `python build.py --pdf`. The home page, contents columns, pager links and the CV's
   "Academic projects" list all update from that one file.

## Updating the CV

Edit `src/content/cv.json`, then run `python build.py --pdf` (uses Edge or Chrome to print `cv.html`).

## Deploying

GitHub Pages serves the `main` branch root, so pushing to `main` updates the live site.
Commit the generated HTML along with the `src/` changes.

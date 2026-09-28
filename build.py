"""Build the portfolio site from src/ into plain HTML files at the repo root.

    python build.py          build every page, then check links and images
    python build.py --pdf    also regenerate assets/cv/Luha-Nihaz-CV.pdf (needs Edge or Chrome)

Content lives in src/content/ (cv.json, semesters/N.json); the shared page shell
is src/templates/layout.html. Text fields may contain inline HTML (<b>, &amp; ...).
Standard library only — no packages to install.
"""
import argparse
import datetime
import functools
import glob
import html
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import threading

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
CV_PDF = "assets/cv/Luha-Nihaz-CV.pdf"
YEAR = datetime.date.today().year


def load(path):
    with open(os.path.join(SRC, path), encoding="utf-8") as f:
        return json.load(f)


def attr(text):
    return html.escape(text, quote=True)


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("  wrote", rel)


# ---------------------------------------------------------------- data

CV = load("content/cv.json")
SEMS = sorted((load(p) for p in glob.glob(os.path.join(SRC, "content/semesters/*.json"))), key=lambda s: s["sem"])
DONE = [s for s in SEMS if s["status"] == "complete"]
NAME = CV["name"]
FULL_NAME = f'{NAME["first"]} {NAME["preferred"]} {NAME["last"]}'
LAYOUT = open(os.path.join(SRC, "templates/layout.html"), encoding="utf-8").read()


def sem_no(s):
    return f'{s["sem"]:02d}'


def project_href(s):
    return f'{s["slug"]}.html'


# ---------------------------------------------------------------- shared shell

NAV = [("Home", "index.html", "home"), ("Work", "index.html#work", "work"),
       ("About", "about.html", "about"), ("CV", "cv.html", "cv")]


def page(rel, *, title, description, main, footer, active, sem=None, extra_head="", body_class=""):
    root = "../" * rel.count("/")
    nav = []
    for label, href, key in NAV:
        cls = [c for c in ("cv-link" if key == "cv" else "", "active" if key == active else "") if c]
        cls_attr = f' class="{" ".join(cls)}"' if cls else ""
        nav.append(f'    <a href="{root}{href}"{cls_attr}>{label}</a>')
    body_attrs = (f' data-sem="{sem}"' if sem else "") + (f' class="{body_class}"' if body_class else "")
    values = {
        "title": title, "description": attr(description), "root": root,
        "brand": f'{NAME["preferred"]} <span>{NAME["last"]}</span>',
        "nav": "\n".join(nav), "main": main.strip("\n"), "footer": footer,
        "body_attrs": body_attrs, "extra_head": extra_head,
    }
    write(rel, re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], LAYOUT))


def copyright_span():
    return f'<span>© <span data-year>{YEAR}</span> {FULL_NAME}</span>'


# ---------------------------------------------------------------- building blocks

def img(root, fig, lazy=True):
    style = f' style="object-position:{fig["position"]}"' if fig.get("position") else ""
    loading = ' loading="lazy"' if lazy else ""
    return f'<img src="{root}assets/img/{fig["src"]}" alt="{attr(fig["alt"])}"{loading}{style}>'


def step_title(b, reveal=False):
    if not b.get("step"):
        return ""
    cls = "step-title reveal" if reveal else "step-title"
    return f'<div class="{cls}"><b>{b["step"]}</b><span>{b["label"]}</span></div>'


def title_stack(h):
    sub = f'<p class="sub">{h["sub"]}</p>' if h.get("sub") else ""
    return f'<div class="title-stack"><h2>{h["title"]}<small>{h["small"]}</small></h2>{sub}</div>'


def block_figure(b, r):
    frame = "frame " if b.get("frame") else ""
    notes = ""
    if b.get("notes"):
        items = "".join(f'<p><b>{n["title"]}</b><br>{n["text"]}</p>' for n in b["notes"])
        notes = f'\n        <div class="grid-3 notes">{items}</div>'
    return (f'      <div class="block reveal">\n        {step_title(b)}\n'
            f'        <figure class="{frame}zoomable">{img(r, b)}</figure>{notes}\n      </div>')


def block_cards(b, r):
    cards = "\n".join(
        f'          <div class="card"><span class="kicker">{c["kicker"]}</span>'
        f'<div class="pair">{c["from"]} <i>→</i> {c["to"]}</div><p>{c["text"]}</p></div>'
        for c in b["items"])
    return f'      <div class="block reveal">\n        {step_title(b)}\n        <div class="cards">\n{cards}\n        </div>\n      </div>'


def block_statement(b, r):
    return f'      <div class="block reveal">\n        {step_title(b)}\n        <p class="statement narrow">{b["text"]}</p>\n      </div>'


def block_steps(b, r):
    items = "\n".join(
        f'        <figure class="reveal zoomable"><span class="n">{i:02d}</span><h3>{s["title"]}</h3>'
        f'{img(r, s)}<p>{s["text"]}</p></figure>'
        for i, s in enumerate(b["items"], 1))
    return f'      <div class="block">\n      <div class="steps">\n{items}\n      </div>\n      </div>'


def block_grid(b, r):
    frame, clip = b.get("frame"), b.get("clip")
    figs = []
    for it in b["items"]:
        cap = f'<figcaption>{it["caption"]}</figcaption>' if it.get("caption") else ""
        if frame == "inner":
            figs.append(f'<figure class="reveal zoomable"><div class="frame">{img(r, it)}</div>{cap}</figure>')
        else:
            cls = " ".join(c for c in ("frame" if frame == "outer" else "", "reveal zoomable", "clip" if clip else "") if c)
            figs.append(f'<figure class="{cls}">{img(r, it)}{cap}</figure>')
    inner = "\n".join("          " + f for f in figs)
    return f'      <div class="block">\n        {step_title(b, reveal=True)}\n        <div class="grid-{b["cols"]}">\n{inner}\n        </div>\n      </div>'


def block_split(b, r):
    fig = b["figure"]
    frame = "frame " if fig.get("frame") else ""
    side = []
    if b.get("step_inside"):
        side.append(step_title(b))
    if b.get("heading"):
        side.append(title_stack(b["heading"]))
    if b.get("kicker"):
        side.append(f'<span class="kicker">{b["kicker"]}</span>')
    side += [f"<p>{p}</p>" for p in b.get("paragraphs", [])]
    if b.get("statement"):
        side.append(f'<p class="statement">{b["statement"]}</p>')
    if b.get("tags"):
        side.append('<div class="tags">' + "".join(f'<span class="tag">{t}</span>' for t in b["tags"]) + "</div>")
    above = "" if b.get("step_inside") else step_title(b, reveal=True)
    side_html = "\n".join("            " + s for s in side)
    return (f'      <div class="block">\n        {above}\n        <div class="split {b.get("layout", "")}">\n'
            f'          <figure class="{frame}reveal zoomable">{img(r, fig)}</figure>\n'
            f'          <div class="reveal split-text">\n{side_html}\n          </div>\n        </div>\n      </div>')


def block_gallery(b, r):
    side = "\n".join(f'        <figure class="reveal zoomable">{img(r, f)}</figure>' for f in b["side"])
    return (f'      <div class="gallery">\n        <figure class="main reveal zoomable">{img(r, b["main"])}</figure>\n'
            f'{side}\n      </div>')


BLOCKS = {"figure": block_figure, "cards": block_cards, "statement": block_statement, "steps": block_steps,
          "grid": block_grid, "split": block_split, "gallery": block_gallery}


def render_section(sec, r):
    tint = " tint" if sec.get("tint") else ""
    head = ""
    if sec.get("head"):
        h = sec["head"]
        head = f'      <div class="head-grid reveal">\n        {title_stack(h)}\n        <p>{h["intro"]}</p>\n      </div>\n\n'
    blocks = "\n\n".join(BLOCKS[b["type"]](b, r) for b in sec["blocks"])
    return f'  <section class="section{tint}" id="{sec["id"]}">\n    <div class="wrap">\n{head}{blocks}\n    </div>\n  </section>'


def pager(prev, nxt, label="Projects"):
    (ph, ps, pt), (nh, ns, nt) = prev, nxt
    return (f'  <nav class="pager" aria-label="{label}">\n'
            f'    <a href="{ph}"><small>{ps}</small><strong>{pt}</strong></a>\n'
            f'    <a href="{nh}"><small>{ns}</small><strong>{nt}</strong></a>\n  </nav>')


def project_pager(s):
    i = SEMS.index(s)
    contents = ("../index.html#contents", "← Contents", "All semesters")
    if i > 0:
        p = SEMS[i - 1]
        prev = (project_href(p), f"← Previous · Semester {sem_no(p)}", p["title"])
    else:
        prev = contents
    if i < len(SEMS) - 1:
        n = SEMS[i + 1]
        nxt = (project_href(n), f"Next · Semester {sem_no(n)} →", n["title"])
    else:
        nxt = ("../index.html#contents", "Back to →", "All semesters")
    return pager(prev, nxt)


# ---------------------------------------------------------------- pages

def build_project(s):
    r = "../"
    hero = s["hero"]
    contain = " contain" if hero.get("contain") else ""
    first = s["sections"][0]["id"]
    main = f'''
  <section class="p-hero">
    <div class="wrap">
      <div class="reveal">
        <span class="sem">Semester {s["sem"]}</span>
        <h1>{"<br>".join(s["title_lines"])}</h1>
        <p class="loc">{s["location"]}</p>
        <p class="lead">{s["lead"]}</p>
        <a class="scroll-cue" href="#{first}">Explore project</a>
      </div>
      <figure class="media{contain} reveal zoomable">{img(r, hero, lazy=False)}</figure>
    </div>
  </section>

{chr(10).join(render_section(sec, r) + chr(10) for sec in s["sections"])}
{project_pager(s)}
'''
    page(f'projects/{s["slug"]}.html', title=f'{s["title"]} — {NAME["preferred"]} {NAME["last"]}',
         description=s["description"], main=main, active="work", sem=s["sem"],
         footer=f'<span>Semester {sem_no(s)} · {s["title"]}</span>\n  {copyright_span()}')


def build_soon(s):
    n = s["sem"]
    main = f'''
  <section class="soon-hero">
    <span class="big" aria-hidden="true">{n}</span>
    <div class="wrap">
      <div class="reveal">
        <span class="kicker">Semester {sem_no(s)}</span>
        <h1>Coming<br>soon</h1>
        <p>This semester’s project is currently in the studio. Drawings, models and final views will be added here once the work is complete.</p>
        <div class="progress"><div class="bar"></div><small>Work in progress</small></div>
        <a class="btn soon-btn" href="../index.html#work">See completed work <span class="arr">→</span></a>
      </div>
    </div>
  </section>

{project_pager(s)}
'''
    page(f'projects/{s["slug"]}.html', title=f'Semester {n} — {NAME["preferred"]} {NAME["last"]}',
         description=s["description"], main=main, active="work", sem=n,
         footer=f'<span>Semester {sem_no(s)} · Coming soon</span>\n  {copyright_span()}')


def build_home():
    cols = []
    for s in SEMS:
        n = s["sem"]
        href = f'projects/{project_href(s)}'
        if s["status"] == "complete":
            cols.append(f'''        <a class="sem-col reveal" data-sem="{n}" href="{href}" data-img="assets/img/{s["contents_img"]}">
          <span class="img" aria-hidden="true"></span>
          <span class="letters">S<br>E<br>M<b>{n}</b></span>
          <span class="foot"><span class="title">{s["title"]}</span><span class="pg">{s["page"]}</span></span>
        </a>''')
        else:
            cols.append(f'''        <a class="sem-col soon reveal" data-sem="{n}" href="{href}">
          <span class="letters">S<br>E<br>M<b>{n}</b></span>
          <span class="foot"><span class="title">Coming soon</span><span class="pg">00</span></span>
        </a>''')

    features = []
    for s in DONE:
        f = s["feature"]
        contain = " contain" if f.get("contain") else ""
        href = f'projects/{project_href(s)}'
        features.append(f'''      <article class="feature" data-sem="{s["sem"]}">
        <a class="feature-media{contain} reveal" href="{href}">{img("", f)}</a>
        <div class="reveal">
          <span class="kicker">Semester {sem_no(s)}</span>
          <h3>{s["title"]}</h3>
          <p class="loc">{s["location"]}</p>
          <p>{s["summary"]}</p>
          <a class="btn" href="{href}">View project <span class="arr">→</span></a>
        </div>
      </article>''')

    edu, job = CV["education"][0], CV["experience"][0]
    tools = " · ".join(t["name"] for t in CV["software"])
    main = f'''
  <section class="cover">
    <div class="wrap">
      <div class="reveal">
        <h1>PORTFOLIO</h1>
        <p class="name">{FULL_NAME}</p>
        <p class="role">{CV["tagline"]}</p>
        <a class="scroll-cue" href="#contents">View contents</a>
      </div>
    </div>
  </section>

  <section class="section tint" id="about">
    <div class="wrap home-about">
      <div class="portrait reveal"><img src="assets/img/{CV["portrait"]}" alt="Portrait of {FULL_NAME}" loading="lazy"></div>
      <div class="reveal">
        <div class="sec-label"><h2>About me</h2></div>
        <p class="fullname">{NAME["first"]} <b>{NAME["preferred"]}</b> {NAME["last"]}</p>
        <p class="bio">{CV["bio"]}</p>
        <dl class="facts">
          <div><dt>Studying</dt><dd>{edu.get("short", edu["title"])}, {edu["place"]} · {edu["years"].replace(" – ", "–")}</dd></div>
          <div><dt>Currently</dt><dd>{job["role"]}, {job.get("org_short", job["org"])}</dd></div>
          <div><dt>Tools</dt><dd>{tools}</dd></div>
        </dl>
        <div class="btn-row">
          <a class="btn" href="about.html">More about me <span class="arr">→</span></a>
          <a class="btn solid" href="{CV_PDF}" download>Download CV <span class="arr">↓</span></a>
        </div>
      </div>
    </div>
  </section>

  <section class="section" id="contents">
    <div class="wrap">
      <div class="contents-head reveal">
        <h2>Content</h2>
        <p>Work organised by semester, from a first conceptual study to an urban mixed-use building. Hover a column to preview the project.</p>
      </div>

      <div class="sems">
{chr(10).join(cols)}
      </div>
    </div>
  </section>

  <section class="section tint" id="work">
    <div class="wrap">
{(chr(10) + chr(10)).join(features)}
    </div>
  </section>
'''
    page("index.html", title=f'{NAME["preferred"]} {NAME["last"]} — Architectural Design Portfolio',
         description=f'Architectural design portfolio of {FULL_NAME}, Architectural Design student at the Maldives National University.',
         main=main, active="home",
         footer=f'{copyright_span()}\n  <a href="about.html">About &amp; contact</a>')


def timeline(items):
    return "\n".join(f'        <li><strong>{a}</strong><em>{b}</em><span class="dot"></span><time>{t}</time></li>'
                     for a, b, t in items)


def build_about():
    c = CV["contact"]
    edu = [(e.get("short", e["title"]), e["place"], e["years"].replace(" – ", "–")) for e in reversed(CV["education"])]
    exp = [(x.get("org_short", x["org"]), x["role"], x["years"].replace(" – ", "–")) for x in reversed(CV["experience"])]
    skills = "\n".join(f'        <div class="skill"><div class="ico">{t["abbr"]}</div><span>{t["name"]}</span></div>'
                       for t in CV["software"])
    first = DONE[0] if DONE else SEMS[0]
    main = f'''
  <section class="about-hero">
    <div class="wrap">
      <div class="portrait reveal"><img src="assets/img/{CV["portrait"]}" alt="Portrait of {FULL_NAME}"></div>
      <div class="reveal">
        <h1>About me</h1>
        <p class="fullname">{NAME["first"]} <b>{NAME["preferred"]}</b> {NAME["last"]}</p>
        <p class="bio">{CV["bio"]}</p>
        <div class="contact" id="contact">
          <a href="mailto:{c["email"]}">{c["email"]}</a>
          <a href="tel:{c["phone"]["tel"]}">{c["phone"]["display"]}</a>
          <a href="{CV_PDF}" download>Download CV (PDF)</a>
        </div>
      </div>
    </div>
  </section>

  <section class="section tint">
    <div class="wrap">
      <div class="sec-label reveal"><h2>Academics</h2></div>
      <ol class="timeline reveal">
{timeline(edu)}
      </ol>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="sec-label reveal"><h2>Experience</h2></div>
      <ol class="timeline reveal">
{timeline(exp)}
      </ol>
    </div>
  </section>

  <section class="section tint">
    <div class="wrap">
      <div class="sec-label reveal"><h2>Skills</h2></div>
      <div class="skills reveal">
{skills}
      </div>
    </div>
  </section>

{pager(("index.html", "← Back", "Home"), (f"projects/{project_href(first)}", "Start with →", f"Semester {sem_no(first)}"), label="More")}
'''
    page("about.html", title=f'About — {NAME["preferred"]} {NAME["last"]}',
         description=f'About {FULL_NAME}: academics, experience and skills.',
         main=main, active="about",
         footer=f'{copyright_span()}\n  <a href="index.html#work">Selected work</a>')


def cv_timeline(items):
    return "\n".join(f'          <li><time>{t}</time><div><strong>{a}</strong><em>{b}</em></div></li>' for t, a, b in items)


def build_cv():
    c = CV["contact"]
    edu = [(e["years"], e["title"], e["place"]) for e in CV["education"]]
    exp = [(x["years"], x["role"], x["org"]) for x in CV["experience"]]
    projects = [(f'Semester {s["sem"]}', s["title"], s["cv_line"]) for s in reversed(DONE)]
    software = "".join(f"<li>{t['name']}</li>" for t in CV["software"])
    skills = "\n".join(f"          <li>{s}</li>" for s in CV["design_skills"])
    main = f'''
  <div class="cv-toolbar wrap">
    <span class="kicker">Curriculum Vitae</span>
    <a class="btn solid" href="{CV_PDF}" download>Download PDF <span class="arr">↓</span></a>
  </div>

  <article class="cv-sheet">
    <aside class="cv-side">
      <img class="cv-photo" src="assets/img/{CV["portrait"]}" alt="Portrait of {FULL_NAME}">

      <section>
        <h3>Contact</h3>
        <ul class="cv-list">
          <li><small>Email</small><a href="mailto:{c["email"]}">{c["email"]}</a></li>
          <li><small>Phone</small><a href="tel:{c["phone"]["tel"]}">{c["phone"]["display"]}</a></li>
          <li><small>Online portfolio</small><a href="{c["website"]["url"]}">{c["website"]["display"]}</a></li>
        </ul>
      </section>

      <section>
        <h3>Software</h3>
        <ul class="cv-skills">{software}</ul>
      </section>

      <section>
        <h3>Design skills</h3>
        <ul class="cv-plain">
{skills}
        </ul>
      </section>
    </aside>

    <div class="cv-main">
      <header class="cv-head">
        <h1>{NAME["first"]} <span>{NAME["preferred"]}</span> {NAME["last"]}</h1>
        <p class="cv-role">{CV["role"]}</p>
      </header>

      <section>
        <h2>Profile</h2>
        <p>{CV["profile"]}</p>
      </section>

      <section>
        <h2>Education</h2>
        <ol class="cv-timeline">
{cv_timeline(edu)}
        </ol>
      </section>

      <section>
        <h2>Experience</h2>
        <ol class="cv-timeline">
{cv_timeline(exp)}
        </ol>
      </section>

      <section>
        <h2>Academic projects</h2>
        <ol class="cv-timeline">
{cv_timeline(projects)}
        </ol>
      </section>
    </div>
  </article>
'''
    page("cv.html", title=f"CV — {FULL_NAME}",
         description=f'Curriculum Vitae of {FULL_NAME}, Architectural Design student.',
         main=main, active="cv", body_class="cv-page",
         extra_head='\n<link rel="stylesheet" href="css/cv.css">',
         footer=f'{copyright_span()}\n  <a href="{CV_PDF}" download>Download CV (PDF)</a>')


# ---------------------------------------------------------------- checks & PDF

def check_links():
    bad = []
    for f in glob.glob(os.path.join(ROOT, "*.html")) + glob.glob(os.path.join(ROOT, "projects/*.html")):
        text = open(f, encoding="utf-8").read()
        refs = re.findall(r'(?:href|src|data-img)="([^"#]+)', text) + re.findall(r'url\("?([^")]+)', text)
        for u in refs:
            if u.startswith(("http", "mailto:", "tel:")):
                continue
            if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(f), u))):
                bad.append(f"{os.path.relpath(f, ROOT)} -> {u}")
    return bad


def find_browser():
    candidates = [
        shutil.which("msedge"), shutil.which("chrome"), shutil.which("google-chrome"), shutil.which("chromium"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    return next((c for c in candidates if c and os.path.exists(c)), None)


def build_pdf():
    browser = find_browser()
    if not browser:
        sys.exit("  no Edge/Chrome found - cannot build the CV PDF")
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    out = os.path.join(ROOT, CV_PDF)
    try:
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--virtual-time-budget=8000", f"--print-to-pdf={out}",
                        f"http://127.0.0.1:{server.server_port}/cv.html"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    finally:
        server.shutdown()
    print("  wrote", CV_PDF)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", action="store_true", help="also regenerate the CV PDF")
    args = ap.parse_args()

    print("Building pages")
    build_home()
    build_about()
    build_cv()
    for s in SEMS:
        (build_project if s["status"] == "complete" else build_soon)(s)
    if args.pdf:
        build_pdf()

    bad = check_links()
    if bad:
        print("Broken links:\n  " + "\n  ".join(bad))
        sys.exit(1)
    print("Done - all links and images OK")


if __name__ == "__main__":
    main()

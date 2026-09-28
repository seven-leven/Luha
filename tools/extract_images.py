"""Crop figures out of the portfolio PDF (coords in PDF points, page = 595pt square)."""
import fitz, os, sys
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "SEM 123 low res.pdf")
OUT = os.path.join(ROOT, "assets", "img")
DPI = 260

CROPS = {
    # about
    "about/portrait":        (3,  (108, 82, 218, 213)),
    # sem 1 — drop of success
    "sem1/platonic-solids":  (5,  (134, 212, 558, 300)),
    "sem1/journey":          (5,  (155, 482, 565, 537)),
    "sem1/step-1":           (6,  (88, 146, 188, 233)),
    "sem1/step-2":           (6,  (328, 146, 428, 233)),
    "sem1/step-3":           (6,  (88, 318, 198, 419)),
    "sem1/step-4":           (6,  (303, 318, 428, 411)),
    "sem1/model-annotated":  (7,  (105, 128, 580, 505)),
    "sem1/model":            (7,  (216, 128, 460, 505)),
    # sem 2 — reef ray
    "sem2/manta":            (9,  (147, 152, 310, 274)),
    "sem2/form-development": (9,  (143, 440, 570, 550)),
    "sem2/bubble-diagram":   (10, (93, 114, 352, 304)),
    "sem2/floor-plan":       (10, (93, 328, 430, 574)),
    "sem2/render-main":      (11, (130, 109, 547, 406)),
    "sem2/render-left":      (11, (130, 422, 330, 546)),
    "sem2/render-right":     (11, (350, 422, 548, 546)),
    # sem 3 — streamline villa
    "sem3/site":             (13, (118, 140, 570, 294)),
    "sem3/flow-study":       (13, (145, 450, 270, 535)),
    "sem3/facade-pattern":   (13, (302, 450, 404, 537)),
    "sem3/facade-applied":   (13, (433, 453, 558, 537)),
    "sem3/bubble-diagrams":  (14, (42, 118, 512, 412)),
    "sem3/form-development": (14, (62, 456, 502, 562)),
    "sem3/plan-ground":      (15, (96, 48, 595, 305)),
    "sem3/plan-first":       (15, (92, 315, 595, 562)),
    "sem3/plan-typical":     (16, (10, 46, 523, 297)),
    "sem3/plan-terrace":     (16, (10, 308, 523, 558)),
    "sem3/render-1":         (17, (90, 127, 323, 364)),
    "sem3/render-2":         (17, (340, 127, 572, 364)),
    "sem3/render-3":         (17, (90, 385, 325, 528)),
    "sem3/render-4":         (17, (339, 385, 574, 528)),
}

# areas (page pt) painted white after cropping, to drop labels that touch a figure
WHITEOUT = {
    "sem1/model": [(378, 136, 460, 205)],
    "sem2/bubble-diagram": [(318, 128, 352, 206)],
}

doc = fitz.open(SRC)
for name, (page, box) in CROPS.items():
    rect = fitz.Rect(box)
    pix = doc[page - 1].get_pixmap(dpi=DPI, clip=rect)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    s = DPI / 72
    draw = ImageDraw.Draw(img)
    for (x0, y0, x1, y1) in WHITEOUT.get(name, []):
        draw.rectangle([(x0 - rect.x0) * s, (y0 - rect.y0) * s, (x1 - rect.x0) * s, (y1 - rect.y0) * s], fill="white")
    path = os.path.join(OUT, name + ".jpg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, quality=86, optimize=True, progressive=True)
    print(name, img.size)

# clean cover texture (a single CMYK image layer on page 1)
pix = fitz.Pixmap(fitz.csRGB, fitz.Pixmap(doc, 1156))
img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
img.save(os.path.join(OUT, "cover-texture.jpg"), quality=82, optimize=True, progressive=True)
print("cover-texture", img.size)

#!/usr/bin/env python3
"""Dessine le dé à fabriquer du « Fermier au chapeau de paille » sur une page A5, dans un PDF à part.

Patron de cube en croix, faces de 29 mm : deux faces opposées font toujours 7. Chaque face est blanche,
bordée d'un filet bleu nuit comme l'encadré du dé ; les points sont le diamant en voxel de Manon.
Les traits pleins se découpent, les pointillés bleus se plient, les languettes bleu pâle se collent.

Produit Impression/LeFermierAuChapeauDePaille_De.pdf, pour accompagner le livret. Nécessite Google Chrome.
Usage, depuis la racine du dépôt : python source/construire_de.py (avec le venv qui contient pypdf)
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from construire_livret import CSS as CSS_LIVRET, TITRE_POLICE, imprimer, separateur  # noqa: E402
from construire_site import AUTEURS, TITRE  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE.parent / "Impression" / "LeFermierAuChapeauDePaille_De.pdf"
PATTE = (RACINE / "images" / "objets" / "diamant.png").as_uri()

FACE = 29          # côté d'une face, en mm
LANGUETTE = 7      # profondeur des languettes, en mm
MARGE = 1          # marge autour du dessin, pour que les traits extérieurs ne soient pas coupés
NUIT, OR, OR_FONCE, CREME = "#1a1a1a", "#14507f", "#3aa0e8", "#eef8ff"

# Position (colonne, ligne) de chaque face dans la croix et sa valeur : A en haut, puis B, C, D
# dans la colonne du milieu, L et R de part et d'autre de B. Opposées : A–C, B–D, L–R.
FACES = {"A": ((1, 0), 2), "L": ((0, 1), 3), "B": ((1, 1), 1), "R": ((2, 1), 4),
         "C": ((1, 2), 5), "D": ((1, 3), 6)}

# Points de chaque valeur, en fractions de la face
POINTS = {
    1: [(0.5, 0.5)],
    2: [(0.3, 0.3), (0.7, 0.7)],
    3: [(0.29, 0.29), (0.5, 0.5), (0.71, 0.71)],
    4: [(0.3, 0.3), (0.7, 0.3), (0.3, 0.7), (0.7, 0.7)],
    5: [(0.29, 0.29), (0.71, 0.29), (0.5, 0.5), (0.29, 0.71), (0.71, 0.71)],
    6: [(0.31, 0.26), (0.69, 0.26), (0.31, 0.5), (0.69, 0.5), (0.31, 0.74), (0.69, 0.74)],
}

# Languettes : (face, côté). Sept collages pour fermer le cube.
LANGUETTES = [("A", "haut"), ("L", "haut"), ("L", "gauche"), ("L", "bas"),
              ("R", "haut"), ("R", "droite"), ("R", "bas")]


def languette(x, y, cote):
    """Trapèze collé au bord d'une face dont le coin haut gauche est (x, y)."""
    f, l, r = FACE, LANGUETTE, LANGUETTE * 0.9
    points = {
        "haut": [(x, y), (x + r, y - l), (x + f - r, y - l), (x + f, y)],
        "bas": [(x, y + f), (x + r, y + f + l), (x + f - r, y + f + l), (x + f, y + f)],
        "gauche": [(x, y), (x - l, y + r), (x - l, y + f - r), (x, y + f)],
        "droite": [(x + f, y), (x + f + l, y + r), (x + f + l, y + f - r), (x + f, y + f)],
    }[cote]
    trace = " ".join(f"{px:.2f},{py:.2f}" for px, py in points)
    return f'<polygon points="{trace}" fill="{CREME}" stroke="{NUIT}" stroke-width="0.35"/>'


def patron():
    ox, oy = LANGUETTE + MARGE, LANGUETTE + MARGE
    largeur, hauteur = 3 * FACE + 2 * (LANGUETTE + MARGE), 4 * FACE + 2 * (LANGUETTE + MARGE)
    dessin = []
    for nom, cote in LANGUETTES:
        (c, li), _ = FACES[nom]
        dessin.append(languette(ox + c * FACE, oy + li * FACE, cote))
    for (c, li), valeur in FACES.values():
        x, y = ox + c * FACE, oy + li * FACE
        dessin.append(f'<rect x="{x}" y="{y}" width="{FACE}" height="{FACE}" fill="#fff"/>')
        # Un filet bleu à l'intérieur de chaque face
        dessin.append(f'<rect x="{x + 2.2}" y="{y + 2.2}" width="{FACE - 4.4}" height="{FACE - 4.4}" rx="1.6" '
                      f'fill="none" stroke="{OR}" stroke-width="0.5"/>')
        # Le diamant à la place de chaque point, centré sur sa position
        taille = 7 if valeur < 6 else 6
        for px, py in POINTS[valeur]:
            dessin.append(f'<image href="{PATTE}" x="{x + px * FACE - taille / 2:.2f}" y="{y + py * FACE - taille / 2:.2f}" '
                          f'width="{taille}" height="{taille}"/>')
    # Contour découpé en trait plein, puis pliures en pointillés par-dessus
    contour = [(1, 0), (2, 0), (2, 1), (3, 1), (3, 2), (2, 2), (2, 4), (1, 4), (1, 2), (0, 2), (0, 1), (1, 1)]
    trace = " ".join(f"{ox + c * FACE},{oy + li * FACE}" for c, li in contour)
    dessin.append(f'<polygon points="{trace}" fill="none" stroke="{NUIT}" stroke-width="0.6"/>')
    plis = [((1, 1), (2, 1)), ((1, 2), (2, 2)), ((1, 3), (2, 3)),    # sous A, sous B, sous C
            ((1, 1), (1, 2)), ((2, 1), (2, 2))]                        # de part et d'autre de B
    for (x1, y1), (x2, y2) in plis:
        dessin.append(f'<line x1="{ox + x1 * FACE}" y1="{oy + y1 * FACE}" x2="{ox + x2 * FACE}" '
                      f'y2="{oy + y2 * FACE}" stroke="{OR_FONCE}" stroke-width="0.45" stroke-dasharray="1.6 1.2"/>')
    for nom, cote in LANGUETTES:   # pli à la base de chaque languette
        (c, li), _ = FACES[nom]
        x, y = ox + c * FACE, oy + li * FACE
        bord = {"haut": (x, y, x + FACE, y), "bas": (x, y + FACE, x + FACE, y + FACE),
                "gauche": (x, y, x, y + FACE), "droite": (x + FACE, y, x + FACE, y + FACE)}[cote]
        dessin.append(f'<line x1="{bord[0]}" y1="{bord[1]}" x2="{bord[2]}" y2="{bord[3]}" '
                      f'stroke="{OR_FONCE}" stroke-width="0.45" stroke-dasharray="1.6 1.2"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{largeur}mm" height="{hauteur}mm" '
            f'viewBox="0 0 {largeur} {hauteur}">{"".join(dessin)}</svg>')


def centrer_verticalement(pdf):
    """Décale le contenu de chaque page pour laisser le même blanc en haut et en bas : la page est rendue en
    image, on mesure la zone imprimée, puis on la déplace du demi-écart."""
    import subprocess
    from pypdf import PdfReader, PdfWriter, Transformation
    ecrivain = PdfWriter(clone_from=str(pdf))   # pypdf 7 : on transforme les pages déjà rattachées à l'écrivain
    for n, page in enumerate(ecrivain.pages, start=1):
        ppm = subprocess.run(["pdftoppm", "-r", "50", "-gray", "-f", str(n), "-l", str(n), str(pdf)],
                             capture_output=True, check=True).stdout
        # en-tête P5 : « P5\nlargeur hauteur\n255\n » puis un octet par pixel
        entete = ppm.split(b"\n", 3)
        largeur, hauteur = map(int, entete[1].split())
        pixels = entete[3]
        lignes = [y for y in range(hauteur) if min(pixels[y * largeur:(y + 1) * largeur]) < 235]
        if lignes:
            haut, bas = lignes[0], hauteur - 1 - lignes[-1]
            decalage = (bas - haut) / 2 * 72 / 50          # en points, vers le bas si le contenu est trop haut
            page.add_transformation(Transformation().translate(0, -decalage))
    with open(pdf, "wb") as f:
        ecrivain.write(f)


def construire():
    css = CSS_LIVRET.split("@page {")[0] + f"""
@page {{ size: 148mm 210mm; margin: 12mm; }}
* {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; font-variant-ligatures: none; }}
html {{ font-family: "Source Serif 4", serif; font-size: 11pt; line-height: 1.45; color: {NUIT}; }}
body {{ margin: 0; text-align: center; }}
h1 {{ font-family: {TITRE_POLICE}; font-weight: 600; font-size: 22pt; color: {NUIT}; margin: 0; }}
h1 span {{ background: linear-gradient(transparent 62%, #f7c531 62% 92%, transparent 92%); }}
.consigne {{ margin: 0 auto 3mm; max-width: 112mm; }}
.separateur {{ display: flex; align-items: center; justify-content: center; gap: 2.5mm; margin: 2.5mm 0 3mm; }}
.separateur .trait {{ width: 14mm; height: 0.6mm; }}
.separateur img {{ width: 6mm; height: 6mm; object-fit: contain; }}
.patron {{ display: flex; justify-content: center; }}
.signature {{ font-style: italic; font-size: 11pt; color: #5c6670; margin-top: 2mm; }}
"""
    page = (
        f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>{css}</style></head><body>'
        f'<h1><span>Ton dé à fabriquer</span></h1>{separateur("diamant")}'
        '<p class="consigne">Découpe le long des traits pleins, plie le long des pointillés, puis colle '
        "les languettes à l'intérieur. Sur un dé, deux faces opposées font toujours 7.</p>"
        f'<div class="patron">{patron()}</div>'
        f'<p class="signature">{TITRE}, une histoire par {AUTEURS}</p></body></html>'
    )
    SORTIE.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as dossier:
        source = Path(dossier) / "de.html"
        source.write_text(page, encoding="utf-8")
        imprimer(source, SORTIE)
    centrer_verticalement(SORTIE)
    print(SORTIE)


if __name__ == "__main__":
    construire()

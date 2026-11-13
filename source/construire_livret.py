#!/usr/bin/env python3
"""Construit le livret imprimable du « Fermier au chapeau de paille » à partir de source/texte.md.

Même chaîne que les autres livres de l'atelier (pages de 124 × 186 mm, renvois avec le numéro de page, imposition
sur A4), dans la DA « Ciel d'été » du site : texte et titres noirs, titres en Pixelify Sans surlignés de jaune
paille, étiquette du numéro bleu ciel, encadré du dé bleu nuit à ombre jaune, séparateurs avec les objets en
voxel de Manon (diamant, flamme, œil, en alternance le long de la lecture).

Particularité du Fermier (demande de Manon) : chaque chapitre s'ouvre sur son illustration A5 en pleine page, à
fond perdu et sans texte ; le texte commence à la page suivante. Les illustrations sont mises au format de la
page par source/preparer_illustrations_livret.py (images/livret/), sans recadrage.

Ordre : couverture, résumé, histoire, arbre (deux pages), « Comment est née cette histoire », pages
d'illustrations supplémentaires si besoin (multiple de 4, jamais de page blanche), quatrième de couverture.

Produit dans le dossier Impression du livre : LeFermierAuChapeauDePaille_Livret_lecture.pdf et les impositions
A4 bord court et bord long. Nécessite Google Chrome, pdftotext (poppler), pypdf et segno.
Usage, depuis la racine du dépôt : python3 source/construire_livret.py
"""
import base64
import html
import io
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import segno
from pypdf import PageObject, PdfReader, PdfWriter, Transformation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from construire_site import (AUTEURS, AVERTISSEMENT_COURT, CITATION, CONTEXTE, SYNOPSIS, TITRE,  # noqa: E402
                             illustration, lire_chapitres, lire_choix, lire_mention, objet_du_chapitre)

RACINE = Path(__file__).resolve().parent.parent
IMPRESSION = RACINE.parent / "Impression"
NOM = "LeFermierAuChapeauDePaille"
ADRESSE = "https://labaixbidouille.github.io/le-fermier-au-chapeau-de-paille/"

MM = 72 / 25.4
LARGEUR_PAGE, HAUTEUR_PAGE = 124, 186          # mm
A4_L, A4_H = 297 * MM, 210 * MM
ENCRE, GRIS, CIEL, NUIT, NUIT_CLAIR, PAILLE = "#1a1a1a", "#5c6670", "#3aa0e8", "#14507f", "#eef8ff", "#f7c531"
TRAITS = {"diamant": "#3cc8d8", "flamme": "#f07a1a", "oeil": "#1f9a5c"}
# Illustrations carrées du site, en pleine largeur, pour compléter le livret à un multiple de 4 pages
COMPLEMENTS = [11, 18, 15]


def uri(chemin):
    return Path(chemin).as_uri()


def police(nom, fichier, poids="400 800", italique=False, plage=""):
    return (f'@font-face {{ font-family: "{nom}"; font-weight: {poids}; {"font-style: italic; " if italique else ""}'
            f'src: url("{uri(RACINE / "fonts" / fichier)}");{plage} }}')


TITRE_POLICE = '"Chiffres", "Pixelify Sans", monospace'
SURLIGNE = f"background: linear-gradient(transparent 62%, {PAILLE} 62% 92%, transparent 92%);"

CSS = "\n".join([police("Pixelify Sans", "PixelifySans.woff2"),
                 police("Chiffres", "ChiffresBricolage.woff2", plage=" unicode-range: U+30-39;"),
                 police("Source Serif 4", "SourceSerif4.woff2"),
                 police("Source Serif 4", "SourceSerif4-italique.woff2", italique=True)]) + f"""
@page {{
  size: {LARGEUR_PAGE}mm {HAUTEUR_PAGE}mm;
  margin: 13mm 12mm 16mm 12mm;
  @bottom-center {{ content: counter(page); font-family: "Source Serif 4"; font-size: 9pt; color: {GRIS}; }}
}}
@page sans-numero {{ @bottom-center {{ content: none; }} }}
@page plein {{ margin: 0; @bottom-center {{ content: none; }} }}

* {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; box-sizing: border-box; font-variant-ligatures: none; }}
html {{ font-family: "Source Serif 4", serif; font-size: 11pt; line-height: 1.48; color: {ENCRE}; hyphens: none; }}
body {{ margin: 0; }}
p {{ margin: 0 0 0.55em; orphans: 2; widows: 2; }}
.page-seule {{ break-before: page; }}
.sans-numero {{ page: sans-numero; }}
.marque {{ font-size: 1pt; color: #fff; }}

/* Illustration en pleine page, à fond perdu (l'image est déjà au format de la page) */
.pleine {{ page: plein; break-before: page; position: relative; height: 185.5mm; overflow: hidden; }}
.pleine img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
.pleine .marque {{ position: absolute; left: 2mm; top: 2mm; }}

/* Couverture : l'image A5 de Manon en pleine page, le titre dans le ciel de nuit */
.couverture {{ page: plein; position: relative; height: 185.5mm; overflow: hidden; }}
.couverture img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
.couverture .titre {{ position: absolute; left: 8mm; right: 8mm; top: 11mm; text-align: center; }}
.couverture .surtitre {{ display: inline-block; background: rgba(255, 255, 255, 0.92); border-radius: 10mm;
  padding: 1.1mm 3.6mm 0.9mm; font-size: 7.5pt; font-style: italic; color: {ENCRE}; }}
.couverture h1 {{ margin: 3mm 0 2mm; font-family: {TITRE_POLICE}; font-weight: 600; font-size: 25pt; line-height: 1.22; }}
.couverture h1 span {{ background: {PAILLE}; color: {ENCRE}; padding: 0 1.5mm; box-decoration-break: clone;
  -webkit-box-decoration-break: clone; }}
.couverture .noms {{ font-style: italic; font-size: 13pt; color: #fff; text-shadow: 0 1px 3px rgba(0, 0, 0, 0.7); }}
.couverture .mention {{ position: absolute; left: 10mm; right: 10mm; bottom: 4.5mm; text-align: center; font-size: 6.5pt;
  font-style: italic; color: #fff; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.9); }}

/* Page 2 : le résumé */
.resume {{ height: 156mm; display: flex; flex-direction: column; justify-content: center; text-align: center; }}
.resume .titre-livre {{ font-family: {TITRE_POLICE}; font-weight: 600; font-size: 15pt; line-height: 1.25; }}
.resume .titre-livre span {{ {SURLIGNE} }}
.resume .noms {{ font-style: italic; margin-top: 2mm; }}
.resume .texte {{ font-size: 12pt; line-height: 1.6; margin-top: 2mm; }}

/* Chapitres */
.ouverture {{ margin: 0 0 4mm; }}
.numero {{ display: inline-block; font-family: {TITRE_POLICE}; font-weight: 600; font-size: 10pt; color: #fff;
  background: {CIEL}; padding: 0.4mm 2.4mm 0.2mm; border-radius: 1mm; }}
h2 {{ font-family: {TITRE_POLICE}; font-weight: 600; font-size: 18pt; line-height: 1.2; margin: 2mm 0 0; }}
h2 span {{ {SURLIGNE} box-decoration-break: clone; -webkit-box-decoration-break: clone; }}
/* Fins de chapitre trop courtes : seul le texte change (jamais sous 11 pt, jamais les images) ; on essaie de le
   resserrer pour gagner une page, puis de l'aérer pour que la dernière page se remplisse */
.serre {{ line-height: 1.4; }}
.serre p {{ margin-bottom: 0.45em; }}
.serre2 {{ line-height: 1.34; }}
.serre2 p {{ margin-bottom: 0.35em; }}
.serre3 {{ line-height: 1.27; }}
.serre3 p {{ margin-bottom: 0.25em; }}
.serre3 .separateur {{ margin: 2.5mm 0 2mm; }}
.aere {{ line-height: 1.6; }}
.aere p {{ margin-bottom: 0.8em; }}
.aere2 {{ line-height: 1.7; }}
.aere2 p {{ margin-bottom: 1em; }}
/* Le dernier paragraphe, le séparateur et l'encadré (ou le renvoi) restent ensemble */
.suite {{ break-inside: avoid; }}

/* Fin de chapitre : séparateur (objet en voxel entre deux traits), puis l'encadré du dé ou le renvoi.
   Le dernier paragraphe peut rester sur la page d'avant ; seuls le séparateur et l'encadré restent ensemble. */
.separateur {{ display: flex; align-items: center; justify-content: center; gap: 3mm; margin: 4mm 0 3.5mm; break-after: avoid; }}
.separateur .trait {{ width: 14mm; height: 0.7mm; }}
.separateur img {{ width: 8mm; height: 8mm; object-fit: contain; }}
.encadre {{ border: 0.8mm solid {NUIT}; box-shadow: 1.3mm 1.3mm 0 {PAILLE}; background: {NUIT_CLAIR};
  padding: 3mm 3.5mm 2.4mm; margin: 0 1.3mm 1.3mm 0; break-inside: avoid; break-before: avoid; }}
.encadre .consigne {{ font-family: {TITRE_POLICE}; font-weight: 600; font-size: 11pt; line-height: 1.3; margin: 0 0 2mm; }}
.tirage {{ display: flex; align-items: baseline; gap: 2.5mm; margin: 1.2mm 0 0; }}
.tirage b {{ flex: none; min-width: 15mm; text-align: center; font-family: {TITRE_POLICE}; font-weight: 600; font-size: 9.5pt;
  color: #fff; background: {NUIT}; padding: 0.2mm 1.5mm 0; }}
.option {{ margin: 1.2mm 0 0; }}
.option i {{ color: {NUIT}; }}
.elan {{ text-align: center; font-family: {TITRE_POLICE}; font-weight: 600; font-size: 11.5pt; color: {NUIT};
  break-before: avoid; margin: 0; }}
.fin {{ text-align: center; font-family: {TITRE_POLICE}; font-weight: 600; font-size: 24pt; break-before: avoid; margin-top: 2mm; }}
.fin span {{ {SURLIGNE} }}

/* L'arbre de l'histoire, en deux pages */
@page arbre {{ margin: 8mm 6mm 9mm; @bottom-center {{ content: none; }} }}
.arbre {{ page: arbre; break-before: page; text-align: center; }}
.arbre h3 {{ font-family: {TITRE_POLICE}; font-weight: 600; font-size: 15pt; margin: 0 0 3mm; }}
.arbre h3 span {{ {SURLIGNE} }}
.arbre .fenetre {{ position: relative; width: 112mm; margin: 0 auto; overflow: hidden; }}
.arbre .fenetre img {{ position: absolute; left: 0; width: 112mm; }}

/* Comment est née cette histoire */
.contexte {{ text-align: center; }}
.contexte h3 {{ font-family: {TITRE_POLICE}; font-weight: 600; font-size: 15pt; line-height: 1.25; margin: 2mm 0 1mm; }}
.contexte h3 span {{ {SURLIGNE} }}
.contexte p {{ font-size: 11pt; }}
.portraits {{ display: flex; justify-content: center; align-items: flex-end; gap: 8mm; }}
.portraits img {{ height: 24mm; width: auto; }}
.portraits img.petit {{ height: 13mm; }}
.citation {{ font-family: {TITRE_POLICE}; font-weight: 600; font-size: 12pt; line-height: 1.35; color: {NUIT}; margin: 3mm 4mm; }}
.citation span {{ display: block; font-family: "Source Serif 4"; font-weight: 400; font-style: italic; font-size: 9pt; color: {GRIS}; margin-top: 1mm; }}

/* Illustrations carrées supplémentaires (pour arriver à un multiple de 4 pages) */
.complement {{ page: plein; break-before: page; height: 185.5mm; display: flex; flex-direction: column; justify-content: center;
  align-items: center; gap: 8mm; background: {NUIT_CLAIR}; }}
.complement .carre {{ width: 100%; display: block; }}
.complement .objet {{ width: 12mm; }}

/* Quatrième de couverture */
.dos {{ height: 156mm; display: flex; flex-direction: column; justify-content: flex-end; text-align: center;
  font-size: 9pt; color: {GRIS}; }}
.dos p {{ font-size: 9pt; }}
.qr {{ margin: 0 0 9mm; color: {ENCRE}; }}
.qr img {{ display: block; width: 24mm; height: 24mm; margin: 0 auto 2mm; }}
.qr .adresse {{ font-size: 7.5pt; color: {GRIS}; }}
"""


def e(texte):
    return html.escape(texte, quote=False)


def cle_de(nom):
    return 0 if nom == "Prologue" else int(nom.split()[-1])


def page(pages, cle):
    return pages.get(cle, "00")


def separateur(objet):
    couleur = TRAITS[objet]
    return (f'<div class="separateur"><span class="trait" style="background:{couleur}"></span>'
            f'<img src="{uri(RACINE / "images" / "objets" / f"{objet}.png")}" alt="">'
            f'<span class="trait" style="background:{couleur}"></span></div>')


VARIANTES = ["serre", "serre2", "serre3", "aere", "aere2"]
REGLAGES = {}                                   # chapitre -> indice dans VARIANTES


def chapitre(ch, pages):
    cle = cle_de(ch["nom"])
    corps, consigne, tirages, options, renvoi, fin = lire_choix(ch)
    image = RACINE / "images" / "livret" / f"{illustration(ch['nom'])}.jpg"
    morceaux = [f'<section class="pleine"><span class="marque">@@CH{cle}@@</span><img src="{uri(image)}" alt=""></section>']
    classe = "page-seule" + (f" {VARIANTES[REGLAGES[cle]]}" if cle in REGLAGES else "")
    numero = "Prologue" if cle == 0 else ch["numero"]
    morceaux.append(f'<section class="{classe}"><div class="ouverture"><span class="numero">{e(numero)}</span>'
                    f'<h2><span>{e(ch["titre"])}</span></h2></div>')
    morceaux += [f"<p>{e(p)}</p>" for p in corps[:-1]]
    suite = [f"<p>{e(corps[-1])}</p>", separateur(objet_du_chapitre(cle))]
    if tirages:
        lignes = "".join(f'<div class="tirage"><b>{d}</b><span>chapitre {n}, page {page(pages, n)}</span></div>'
                         for d, n in tirages)
        suite.append(f'<div class="encadre"><p class="consigne">{e(consigne)} :</p>{lignes}</div>')
    elif options:
        lignes = "".join(f'<p class="option">{e(libelle)}, <i>poursuis au chapitre {n}, page {page(pages, n)}.</i></p>'
                         for libelle, n in options)
        suite.append(f'<div class="encadre"><p class="consigne">{e(consigne)} :</p>{lignes}</div>')
    elif renvoi:
        # Dans un livre, inutile de renvoyer au chapitre suivant : on tourne la page
        texte = "Tourne la page" if renvoi == cle + 1 else f"Poursuis au chapitre {renvoi}, page {page(pages, renvoi)}"
        suite.append(f'<p class="elan">{texte}</p>')
    if fin:
        suite = [f"<p>{e(corps[-1])}</p>", separateur(objet_du_chapitre(cle)), '<p class="fin"><span>Fin</span></p>']
    morceaux.append('<div class="suite">' + "".join(suite) + "</div>")
    morceaux.append("</section>")
    return "".join(morceaux)


def arbre():
    """L'arbre (900 × H px) en deux pages : la coupe tombe entre deux lignes de cartes."""
    svg = RACINE / "images" / "arbre.svg"
    largeur, hauteur = [float(x) for x in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg.read_text()).groups()]
    echelle = 112 / largeur                                    # mm par pixel de l'arbre
    coupe = 24 + 8 * 142 - 14                                  # au-dessus de la 9e ligne de cartes
    pages = []
    for debut, fin, titre in ((0, coupe, "L’arbre de l’histoire"), (coupe, hauteur, "")):
        tete = f'<h3><span>{titre}</span></h3>' if titre else ""
        pages.append(f'<section class="arbre">{tete}<div class="fenetre" style="height:{(fin - debut) * echelle:.1f}mm">'
                     f'<img src="{uri(svg)}" style="top:-{debut * echelle:.1f}mm" alt=""></div></section>')
    return "".join(pages)


def qr_code():
    tampon = io.BytesIO()
    segno.make(ADRESSE, error="m").save(tampon, kind="svg", border=0, dark=ENCRE, xmldecl=False)
    return "data:image/svg+xml;base64," + base64.b64encode(tampon.getvalue()).decode()


def document(pages, complements=0):
    couverture = (
        f'<section class="couverture"><img src="{uri(RACINE / "images" / "livret" / "couverture.jpg")}" alt="">'
        '<div class="titre"><span class="surtitre">Une histoire dont le lecteur est le héros</span>'
        f'<h1><span>{e(TITRE)}</span></h1><div class="noms">{e(AUTEURS)}</div></div>'
        f'<div class="mention">{e(AVERTISSEMENT_COURT)}</div></section>'
        '<section class="page-seule sans-numero"><div class="resume">'
        f'<div class="titre-livre"><span>{e(TITRE)}</span></div><div class="noms">{e(AUTEURS)}</div>'
        f'{separateur("diamant")}<div class="texte">{e(SYNOPSIS)}</div></div></section>'
    )
    chapitres = "".join(chapitre(ch, pages) for ch in lire_chapitres())
    paragraphes = [f"<p>{t.replace(chr(10) * 2, '</p><p>')}</p>" for t in CONTEXTE]
    dessins = RACINE / "images" / "dessins"
    contexte = (
        '<section class="page-seule contexte"><div class="portraits">'
        f'<img src="{uri(dessins / "kevine.png")}" alt=""><img class="petit" src="{uri(dessins / "gertrude.png")}" alt=""></div>'
        f'<h3><span>Comment est née cette histoire</span></h3>{separateur("flamme")}'
        + "".join(paragraphes[:4])
        + f'<div class="citation">« {e(CITATION)} »<span>Antoine et Émile, sur leur fiche récit</span></div>'
        + "".join(paragraphes[4:]) + "</section>"
    )
    objets = ("diamant", "flamme", "oeil")
    supplements = "".join(
        f'<section class="complement"><img class="carre" src="{uri(RACINE / "images" / "chapitres" / f"chapitre-{n:02d}.jpg")}" alt="">'
        f'<img class="objet" src="{uri(RACINE / "images" / "objets" / f"{objets[i % 3]}.png")}" alt=""></section>'
        for i, n in enumerate(COMPLEMENTS[:complements]))
    dos = (
        '<section class="page-seule sans-numero"><div class="dos">'
        f'<div class="qr"><img src="{qr_code()}" alt=""><p>Lis cette histoire en ligne</p>'
        f'<p class="adresse">labaixbidouille.github.io/le-fermier-au-chapeau-de-paille</p></div>'
        f'<p><i>{e(lire_mention())}</i></p>'
        f"<p><b>{e(TITRE)}</b>, une histoire librement inspirée du récit imaginé par Antoine et Émile pendant l’atelier "
        "« La quête du curry, une histoire dont tu es le héros », à la bibliothèque des Deux Ormes "
        "(bibliothèques Méjanes, Aix-en-Provence), en octobre 2026.</p>"
        "<p>Réalisation du livre : Laboratoire d’Aix-périmentation et de Bidouille.</p></div></section>"
    )
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f"<body>{couverture}{chapitres}{arbre()}{contexte}{supplements}{dos}</body></html>")


def imprimer(source_html, pdf):
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=10000", f"--print-to-pdf={pdf}", source_html.as_uri()],
                   check=True, capture_output=True)


def texte_page(pdf, n):
    return subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), str(pdf), "-"],
                          capture_output=True, text=True, check=True).stdout


def reperer_pages(pdf):
    pages = {}
    total = len(PdfReader(str(pdf)).pages)
    for n in range(1, total + 1):
        for cle in re.findall(r"@@CH(\d+)@@", texte_page(pdf, n)):
            pages[int(cle)] = n
    return pages, total


SEUIL_QUEUE = 8


def queues_courtes(pdf, pages):
    """Chapitres dont la dernière page de texte ne porte que quelques lignes (la page de l'illustration ne compte
    pas ; un chapitre qui tient sur une seule page de texte n'est pas concerné)."""
    debuts = sorted((p, cle) for cle, p in pages.items())
    total = len(PdfReader(str(pdf)).pages)
    courtes = set()
    for (debut, cle), (suivant, _) in zip(debuts, debuts[1:] + [(None, None)]):
        if suivant is None:
            continue
        fin = suivant - 1
        if fin <= debut + 1:
            continue
        lignes = [l for l in texte_page(pdf, fin).splitlines() if l.strip() and not l.strip().isdigit()]
        if len(lignes) <= SEUIL_QUEUE:
            courtes.add(cle)
    return courtes


def stabiliser(source, pdf, pages, complements):
    for _ in range(6):
        source.write_text(document(pages, complements), encoding="utf-8")
        imprimer(source, pdf)
        nouvelles, total = reperer_pages(pdf)
        if nouvelles == pages:
            return pages, total
        pages = nouvelles
    raise SystemExit("Les numéros de page ne se stabilisent pas.")


def composer(dossier):
    source, pdf = Path(dossier) / "livret.html", Path(dossier) / "livret.pdf"
    pages, total = stabiliser(source, pdf, {}, 0)
    abandon = set()
    for _ in range(len(VARIANTES) + 1):
        courtes = queues_courtes(pdf, pages) - abandon
        if not courtes:
            break
        for c in courtes:
            suivant = REGLAGES.get(c, -1) + 1
            if suivant < len(VARIANTES):
                REGLAGES[c] = suivant
            else:                                   # aucun réglage ne suffit : on garde la mise en page normale
                REGLAGES.pop(c, None)
                abandon.add(c)
        pages, total = stabiliser(source, pdf, pages, 0)
    complements = (-total) % 4
    if complements:
        pages, total = stabiliser(source, pdf, pages, complements)
        assert total % 4 == 0, total
    return pdf, pages, complements


def traits_de_coupe(dossier):
    x0, y0 = (297 - 2 * LARGEUR_PAGE) / 2, (210 - HAUTEUR_PAGE) / 2
    gauche, droite, haut, bas = x0, x0 + 2 * LARGEUR_PAGE, y0, y0 + HAUTEUR_PAGE
    coupe = [f'<line x1="0" y1="{y}" x2="297" y2="{y}"/>' for y in (haut, bas)]
    coupe += [f'<line x1="{x}" y1="0" x2="{x}" y2="210"/>' for x in (gauche, droite)]
    pli = x0 + LARGEUR_PAGE
    source = Path(dossier) / "traits.html"
    source.write_text(
        '<!doctype html><html><head><style>@page { size: 297mm 210mm; margin: 0; } body { margin: 0; }</style></head>'
        '<body><svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">'
        f'<g stroke="#c9c9c9" stroke-width="0.2">{"".join(coupe)}</g>'
        f'<line x1="{pli}" y1="0" x2="{pli}" y2="210" stroke="#bcd3e6" stroke-width="0.2"/>'
        '</svg></body></html>', encoding="utf-8")
    pdf = Path(dossier) / "traits.pdf"
    imprimer(source, pdf)
    return PdfReader(str(pdf)).pages[0]


def imposer(lecture, traits, sortie, bord_long):
    pages = PdfReader(str(lecture)).pages
    n = len(pages)
    assert n % 4 == 0
    x0 = (A4_L - 2 * LARGEUR_PAGE * MM) / 2
    y0 = (A4_H - HAUTEUR_PAGE * MM) / 2
    ecrivain = PdfWriter()

    def face(gauche, droite, retournee):
        feuille = PageObject.create_blank_page(width=A4_L, height=A4_H)
        feuille.merge_page(traits)
        for indice, x in ((gauche, x0), (droite, x0 + LARGEUR_PAGE * MM)):
            feuille.merge_transformed_page(pages[indice - 1], Transformation().translate(x, y0))
        if retournee:
            feuille.rotate(180)
        ecrivain.add_page(feuille)

    for i in range(n // 4):
        face(n - 2 * i, 1 + 2 * i, False)
        face(2 + 2 * i, n - 1 - 2 * i, bord_long)
    with open(sortie, "wb") as f:
        ecrivain.write(f)


def construire():
    IMPRESSION.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as dossier:
        pdf, pages, complements = composer(dossier)
        lecture = IMPRESSION / f"{NOM}_Livret_lecture.pdf"
        lecture.write_bytes(pdf.read_bytes())
        traits = traits_de_coupe(dossier)
        imposer(lecture, traits, IMPRESSION / f"{NOM}_Livret_A4_bord_court.pdf", bord_long=False)
        imposer(lecture, traits, IMPRESSION / f"{NOM}_Livret_A4_bord_long.pdf", bord_long=True)
    total = len(PdfReader(str(lecture)).pages)
    print(f"{lecture} : {total} pages, soit {total // 4} feuilles A4 recto verso")
    print("Illustrations supplémentaires :", ", ".join(str(c) for c in COMPLEMENTS[:complements]) or "aucune")
    print("Réglages du texte :", ", ".join(f"{c}:{VARIANTES[v]}" for c, v in sorted(REGLAGES.items())) or "aucun")
    print("Fins de chapitre encore courtes :", ", ".join(str(c) for c in sorted(queues_courtes(lecture, pages))) or "aucune")
    print("Pages des chapitres :", ", ".join(f"{k}→{v}" for k, v in sorted(pages.items())))


if __name__ == "__main__":
    construire()

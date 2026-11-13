#!/usr/bin/env python3
"""Dessine images/arbre.svg, l'arbre de toutes les branches du « Fermier au chapeau de paille ».

Chaque étape est une carte blanche avec la vignette de son illustration (la couverture pour le prologue),
l'étiquette bleu ciel du numéro et le titre ; liens bleu nuit, chapeau sur chaque lancer de dé, fin bordée
de jaune paille. Les cartes et les flèches sont calculées à partir de source/texte.md (mêmes règles que le site) :
chaque chapitre est rangé sur la ligne qui suit celle de son prédécesseur le plus bas, les chapitres d'une
même ligne sont répartis autour du centre. Les tirages sont étiquetés « pair » / « impair », le choix du
lecteur du chapitre 5 par le cadeau reçu.

Usage, depuis la racine du dépôt : python3 source/construire_arbre.py
"""
import base64
import html
from io import BytesIO
from pathlib import Path

from construire_site import RACINE, lire_chapitres, lire_choix

SORTIE = RACINE / "images" / "arbre.svg"
# Palette « Ciel d'été » du site
ENCRE, CIEL, NUIT, PAILLE = "#1a1a1a", "#3aa0e8", "#14507f", "#f7c531"
LARGEUR, L_CASE, H_CASE, PAS_Y, ECART, VIGNETTE = 900, 310, 88, 142, 345, 88


def cle(nom):
    return 0 if nom == "Prologue" else int(nom.split()[-1])


def lignes_titre(titre, largeur=22):
    sortie, ligne = [], ""
    for mot in titre.split():
        if ligne and len(ligne) + 1 + len(mot) > largeur:
            sortie.append(ligne)
            ligne = mot
        else:
            ligne = f"{ligne} {mot}".strip()
    return sortie + [ligne]


def police(fichier, nom, style="normal", plage=""):
    code = base64.b64encode((RACINE / "fonts" / fichier).read_bytes()).decode()
    return (f'@font-face {{ font-family: "{nom}"; font-style: {style}; font-weight: 400 800; '
            f'src: url(data:font/woff2;base64,{code}) format("woff2");{plage} }}')


def image_integree(chemin, cote, carre=True):
    """Image réduite et intégrée au SVG (JPEG pour les illustrations, PNG pour le chapeau détouré)."""
    from PIL import Image
    im = Image.open(chemin)
    tampon = BytesIO()
    if im.mode == "RGBA":
        im.thumbnail((cote, cote), Image.LANCZOS)
        im.save(tampon, "PNG", optimize=True)
        return "data:image/png;base64," + base64.b64encode(tampon.getvalue()).decode()
    im = im.convert("RGB")
    c = min(im.size)                                  # carré pris au centre, sans déformer
    im = im.crop(((im.width - c) // 2, (im.height - c) // 2, (im.width + c) // 2, (im.height + c) // 2))
    im = im.resize((cote, cote), Image.LANCZOS)
    im.save(tampon, "JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(tampon.getvalue()).decode()


def construire():
    chapitres = lire_chapitres()
    titres = {cle(ch["nom"]): ch["titre"] for ch in chapitres}
    aretes, tirages_de = [], set()                    # (départ, arrivée, étiquette)
    for ch in chapitres:
        _, _, tirages, options, renvoi, _ = lire_choix(ch)
        a = cle(ch["nom"])
        aretes += [(a, n, d) for d, n in tirages]
        if tirages:
            tirages_de.add(a)
        aretes += [(a, n, libelle.split("reçu ", 1)[-1]) for libelle, n in options]
        if renvoi:
            aretes.append((a, renvoi, ""))
    for a, b, _ in aretes:
        assert b in titres and b > a, f"Renvoi inattendu : {a} -> {b}"

    # Ligne de chaque chapitre : une de plus que son prédécesseur le plus bas
    rang = {0: 0}
    for n in sorted(titres):
        precedents = [rang[a] for a, b, _ in aretes if b == n]
        if precedents:
            rang[n] = max(precedents) + 1
    nb_lignes = max(rang.values()) + 1
    pos = {}
    for r in range(nb_lignes):
        noms = sorted(n for n in rang if rang[n] == r)
        for j, n in enumerate(noms):
            pos[n] = (LARGEUR / 2 + (j - (len(noms) - 1) / 2) * ECART, 24 + r * PAS_Y)
    hauteur = 24 + (nb_lignes - 1) * PAS_Y + H_CASE + 30

    chapeau = image_integree(RACINE / "images" / "chapeau.png", 120)
    traits, pointes, etiquettes, chapeaux = [], [], [], []
    for a, b, texte in aretes:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        depart, arrivee = y1 + H_CASE, y2 - 10
        milieu = depart + (y2 - depart) / 2
        traits.append(f'M{x1:.0f} {depart} V{milieu:.0f} H{x2:.0f} V{arrivee}')
        pointes.append(f'<path d="M{x2 - 8:.0f} {arrivee} h16 l-8 10 z"/>')
        if texte:
            x = x2 if x1 == x2 else (x1 + x2) / 2 + (x2 - x1) / 4
            pixel = texte in ("Pair", "Impair")
            largeur = (18 + len(texte) * 9.5) if pixel else (16 + len(texte) * 7.6)
            etiquettes.append(
                f'<rect x="{x - largeur / 2:.0f}" y="{milieu - 12:.0f}" width="{largeur:.0f}" height="24" fill="{NUIT}"/>'
                f'<text x="{x:.0f}" y="{milieu + 5:.0f}" text-anchor="middle" '
                + ('font-family="Pixelify Sans" font-weight="600" font-size="15"' if pixel
                   else 'font-family="Source Serif 4" font-style="italic" font-size="14"')
                + f' fill="#fff">{html.escape(texte)}</text>')
    for a in tirages_de:
        x, y = pos[a]
        milieu = y + H_CASE + (PAS_Y - H_CASE) / 2
        chapeaux.append(f'<image x="{x - 26:.0f}" y="{milieu - 30:.0f}" width="52" height="34" href="{chapeau}"/>')

    cases = []
    for n, (x, y) in pos.items():
        x0 = x - L_CASE / 2
        fin = n == max(titres)
        image = RACINE / "images" / ("grandes/prologue.jpg" if n == 0 else f"chapitres/chapitre-{n:02d}.jpg")
        numero = "Prologue" if n == 0 else f"Chapitre {n}"
        texte = lignes_titre(titres[n])
        y_titre = y + 60 - (len(texte) - 1) * 9
        l_num = 22 + len(numero) * 8.4
        cases.append(
            f'<g><rect x="{x0 + 2:.0f}" y="{y + 4}" width="{L_CASE}" height="{H_CASE}" rx="8" fill="{PAILLE if fin else "#cfe6f8"}"/>'
            f'<rect x="{x0:.0f}" y="{y}" width="{L_CASE}" height="{H_CASE}" rx="8" fill="#fff"/>'
            f'<clipPath id="v{n}"><rect x="{x0:.0f}" y="{y}" width="{VIGNETTE}" height="{H_CASE}" rx="8"/></clipPath>'
            f'<image x="{x0:.0f}" y="{y}" width="{VIGNETTE}" height="{H_CASE}" preserveAspectRatio="xMidYMid slice" '
            f'clip-path="url(#v{n})" href="{image_integree(image, 160)}"/>'
            f'<rect x="{x0 + VIGNETTE + 12:.0f}" y="{y + 12}" width="{l_num:.0f}" height="21" rx="3" fill="{CIEL}"/>'
            f'<text x="{x0 + VIGNETTE + 12 + l_num / 2:.0f}" y="{y + 28}" text-anchor="middle" font-family="Chiffres, Pixelify Sans" '
            f'font-weight="600" font-size="14" fill="#fff">{numero}</text>'
            + "".join(f'<text x="{x0 + VIGNETTE + 12:.0f}" y="{y_titre + i * 18:.0f}" font-family="Source Serif 4" '
                      f'font-weight="600" font-size="15.5" fill="{ENCRE}">{html.escape(l)}</text>' for i, l in enumerate(texte))
            # Le cadre est tracé en dernier, par-dessus la vignette : il fait le tour de la carte sans interruption
            + f'<rect x="{x0:.0f}" y="{y}" width="{L_CASE}" height="{H_CASE}" rx="8" fill="none" stroke="{PAILLE if fin else NUIT}" '
              f'stroke-width="{4 if fin else 2.5}"/></g>')

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LARGEUR} {hauteur:.0f}" width="{LARGEUR}" '
           f'height="{hauteur:.0f}"><style>{police("PixelifySans.woff2", "Pixelify Sans")}'
           f'{police("ChiffresBricolage.woff2", "Chiffres", plage=" unicode-range: U+30-39;")}'
           f'{police("SourceSerif4.woff2", "Source Serif 4")}{police("SourceSerif4-italique.woff2", "Source Serif 4", "italic")}</style>'
           f'<path d="{" ".join(traits)}" fill="none" stroke="{NUIT}" stroke-width="3" stroke-linejoin="round"/>'
           f'<g fill="{NUIT}">{"".join(pointes)}</g>{"".join(cases)}{"".join(etiquettes)}{"".join(chapeaux)}</svg>')
    SORTIE.write_text(svg, encoding="utf-8")
    print(f"{SORTIE} : {len(pos)} étapes, {len(aretes)} renvois, {nb_lignes} lignes")


if __name__ == "__main__":
    construire()

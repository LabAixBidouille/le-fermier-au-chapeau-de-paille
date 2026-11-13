#!/usr/bin/env python3
"""Dessine images/arbre.svg, l'arbre de toutes les branches du « Fermier au chapeau de paille ».

Les cases et les flèches sont calculées à partir de source/texte.md (mêmes règles de lecture que le site) :
chaque chapitre est rangé sur la ligne qui suit celle de son prédécesseur le plus bas, les chapitres d'une
même ligne sont répartis autour du centre. Les tirages sont étiquetés « pair » / « impair », le choix du
lecteur du chapitre 5 par le cadeau reçu.

Usage, depuis la racine du dépôt : python3 source/construire_arbre.py
"""
import base64
import html
from pathlib import Path

from construire_site import RACINE, lire_chapitres, lire_choix

SORTIE = RACINE / "images" / "arbre.svg"
ECORCE, ENCRE, BRUN, PAILLE, HERBE, TERRE = "#f3e7cb", "#3b2a1a", "#5a3a1c", "#c99a1e", "#2f5d1c", "#866043"
LARGEUR, L_CASE, H_CASE, PAS_Y, ECART = 900, 260, 66, 128, 320


def cle(nom):
    return 0 if nom == "Prologue" else int(nom.split()[-1])


def lignes_titre(titre, largeur=24):
    sortie, ligne = [], ""
    for mot in titre.split():
        if ligne and len(ligne) + 1 + len(mot) > largeur:
            sortie.append(ligne)
            ligne = mot
        else:
            ligne = f"{ligne} {mot}".strip()
    return sortie + [ligne]


def police(fichier, nom, style="normal"):
    code = base64.b64encode((RACINE / "fonts" / fichier).read_bytes()).decode()
    return (f'@font-face {{ font-family: "{nom}"; font-style: {style}; font-weight: 400 700; '
            f'src: url(data:font/woff2;base64,{code}) format("woff2"); }}')


def construire():
    chapitres = lire_chapitres()
    titres = {cle(ch["nom"]): ch["titre"] for ch in chapitres}
    aretes = []                                       # (départ, arrivée, étiquette)
    for ch in chapitres:
        _, _, tirages, options, renvoi, _ = lire_choix(ch)
        a = cle(ch["nom"])
        aretes += [(a, n, d.lower()) for d, n in tirages]
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
            pos[n] = (LARGEUR / 2 + (j - (len(noms) - 1) / 2) * ECART, 30 + r * PAS_Y)
    hauteur = 30 + (nb_lignes - 1) * PAS_Y + H_CASE + 30

    traits, pointes, etiquettes = [], [], []
    for a, b, texte in aretes:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        depart, arrivee = y1 + H_CASE, y2 - 9
        milieu = depart + (y2 - depart) / 2
        traits.append(f'M{x1:.0f} {depart} V{milieu:.0f} H{x2:.0f} V{arrivee}')
        pointes.append(f'<path d="M{x2 - 7:.0f} {arrivee} h14 l-7 9 z"/>')
        if texte:
            x = x2 if x1 == x2 else (x1 + x2) / 2 + (x2 - x1) / 4
            largeur = 14 + len(texte) * 8.2
            etiquettes.append(
                f'<rect x="{x - largeur / 2:.0f}" y="{milieu - 12:.0f}" width="{largeur:.0f}" height="22" fill="{HERBE}"/>'
                f'<text x="{x:.0f}" y="{milieu + 4:.0f}" text-anchor="middle" font-family="Source Serif 4" '
                f'font-style="italic" font-size="14" fill="#fff">{html.escape(texte)}</text>')

    cases = []
    for n, (x, y) in pos.items():
        x0 = x - L_CASE / 2
        fin = n == max(titres)
        numero = "Prologue" if n == 0 else f"Chapitre {n}"
        texte = lignes_titre(titres[n])
        y_titre = y + 43 - (len(texte) - 1) * 8
        cases.append(
            f'<rect x="{x0:.0f}" y="{y}" width="{L_CASE}" height="{H_CASE}" fill="#fffaf0" stroke="{BRUN if not fin else HERBE}" '
            f'stroke-width="{2 if not fin else 3}"/>'
            f'<text x="{x:.0f}" y="{y + 19}" text-anchor="middle" font-family="Pixelify Sans" font-weight="600" '
            f'font-size="14" fill="{PAILLE}">{numero}</text>'
            + "".join(f'<text x="{x:.0f}" y="{y_titre + i * 16:.0f}" text-anchor="middle" font-family="Source Serif 4" '
                      f'font-size="15" fill="{ENCRE}">{html.escape(l)}</text>' for i, l in enumerate(texte)))

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LARGEUR} {hauteur:.0f}" width="{LARGEUR}" '
           f'height="{hauteur:.0f}"><style>{police("PixelifySans.woff2", "Pixelify Sans")}'
           f'{police("SourceSerif4.woff2", "Source Serif 4")}{police("SourceSerif4-italique.woff2", "Source Serif 4", "italic")}</style>'
           f'<path d="{" ".join(traits)}" fill="none" stroke="{TERRE}" stroke-width="2.5"/>'
           f'<g fill="{TERRE}">{"".join(pointes)}</g>{"".join(cases)}{"".join(etiquettes)}</svg>')
    SORTIE.write_text(svg, encoding="utf-8")
    print(f"{SORTIE} : {len(pos)} étapes, {len(aretes)} renvois, {nb_lignes} lignes")


if __name__ == "__main__":
    construire()

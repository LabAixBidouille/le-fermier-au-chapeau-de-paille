#!/usr/bin/env python3
"""Adapte les illustrations A5 (ratio 1,419) au format des pages du livret (124 × 186 mm, ratio 1,5) sans les
recadrer : on prolonge le bord le plus uni (haut ou bas) par un aplat de sa couleur, sans texture recopiée ni flou. Sorties dans images/livret/, 1500 px de large.

Usage, depuis la racine du dépôt : python3 source/preparer_illustrations_livret.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

RACINE = Path(__file__).resolve().parent.parent
SOURCES = RACINE.parent / "illustrations-minecraft-20-chapitres" / "impression-jpg"
SORTIE = RACINE / "images" / "livret"
LARGEUR = 1500


def source(nom):
    for p in (SOURCES / f"{nom}-A5.jpg", SOURCES / f"{nom}-A5.png", SOURCES / f"{nom}-A5-couleurs.png"):
        if p.exists():
            return p
    raise SystemExit(f"Illustration introuvable : {nom}")


def prolonger(im):
    """Prolonge le bord le plus uni par un aplat : la couleur du bord, lissée sur une large largeur (aucune
    texture recopiée), qui tend doucement vers la couleur moyenne du bord ; raccord en fondu de 30 px."""
    from scipy.ndimage import uniform_filter1d
    a = np.asarray(im).astype(float)
    h, w = a.shape[:2]
    manque = round(w * 1.5) - h
    if manque <= 2:                                                      # déjà au format de la page
        return im, "tel quel"
    gris = a.mean(2)
    haut = gris[:manque].std() <= gris[-manque:].std()
    bord = a[:8].mean(0) if haut else a[-8:].mean(0)                    # une ligne de couleurs (w, 3)
    lisse = uniform_filter1d(bord, size=301, axis=0, mode="nearest")
    moyenne = bord.mean(0)
    t = np.linspace(0, 1, manque)[:, None, None]                         # 0 au raccord, 1 au bord de page
    aplat = lisse[None] * (1 - 0.6 * t) + moyenne[None, None] * (0.6 * t)
    if haut:
        aplat = aplat[::-1]
        out = np.concatenate([aplat, a])
        r = manque
        for k in range(30):                                              # fondu : l'image se fond dans l'aplat
            x = k / 30
            out[r + k] = a[k] * x + aplat[-1] * (1 - x)
    else:
        out = np.concatenate([a, aplat])
        for k in range(30):
            x = k / 30
            out[h - 1 - k] = a[h - 1 - k] * x + aplat[0] * (1 - x)
    return Image.fromarray(out.clip(0, 255).astype("uint8")), "haut" if haut else "bas"


def preparer():
    SORTIE.mkdir(parents=True, exist_ok=True)
    for nom in ["prologue"] + [f"chapitre-{n:02d}" for n in range(1, 21)]:
        im = Image.open(source(nom)).convert("RGB")
        im = im.resize((LARGEUR, round(LARGEUR * im.height / im.width)), Image.LANCZOS)
        im, cote = prolonger(im)
        im.save(SORTIE / f"{nom}.jpg", quality=88)
        print(nom, cote)
    # Couverture : l'image A5 de Manon, prolongée de la même façon
    im = Image.open(RACINE.parent / "Sources" / "couverture-A5.png").convert("RGB")
    im = im.resize((LARGEUR, round(LARGEUR * im.height / im.width)), Image.LANCZOS)
    im, cote = prolonger(im)
    im.save(SORTIE / "couverture.jpg", quality=88)
    nebuleuse(im).save(SORTIE / "couverture-nebuleuse.jpg", quality=90)
    print("couverture", cote)


def nebuleuse(im, haut_mm=9, bas_mm=58):
    """Un halo blanc doux et nuageux, aux bords irréguliers et diffus, peint dans l'image derrière le titre
    (intégré à l'image : rien ne peut se décaler à l'impression ou à l'imposition)."""
    from PIL import ImageFilter
    w, h = im.size
    px = h / 186                                                   # pixels par mm
    hasard = np.random.default_rng(7)
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    cy, cx = (haut_mm + bas_mm) / 2 * px, w / 2
    ry, rx = (bas_mm - haut_mm) / 2 * px, w * 0.40
    # cœur : ellipse au bord progressif (dense derrière le texte, puis s'efface)
    d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    masque = np.clip(1.6 - d, 0, 1) ** 0.9
    # volutes : petites nappes autour du cœur, de taille et d'intensité variées
    for _ in range(40):
        a = hasard.uniform(0, 2 * np.pi)
        k = hasard.uniform(0.7, 1.25)
        bx, by = cx + np.cos(a) * rx * k, cy + np.sin(a) * ry * k
        r = hasard.uniform(0.12, 0.3) * ry * 1.8
        masque = np.maximum(masque, np.clip(1 - np.sqrt((xx - bx) ** 2 + (yy - by) ** 2) / r, 0, 1) ** 1.5
                            * hasard.uniform(0.35, 0.75))
    # grain de nuage : bruit adouci, surtout sur les bords
    for echelle, poids in ((90, 0.45), (30, 0.25)):
        bruit = Image.fromarray((hasard.random((h // echelle + 2, w // echelle + 2)) * 255).astype("uint8"))
        bruit = np.asarray(bruit.resize((w, h), Image.BICUBIC)).astype(float) / 255 - 0.5
        masque = masque + bruit * poids * np.clip(masque * (1 - masque) * 4, 0, 1)
    alpha = Image.fromarray((np.clip(masque, 0, 1) * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(px * 2.2))
    alpha = np.asarray(alpha).astype(float) / 255 * 0.95
    a = np.asarray(im).astype(float)
    out = a * (1 - alpha[..., None]) + np.array([248, 251, 255]) * alpha[..., None]
    return Image.fromarray(out.clip(0, 255).astype("uint8"))

if __name__ == "__main__":
    preparer()

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
    print("couverture", cote)


if __name__ == "__main__":
    preparer()

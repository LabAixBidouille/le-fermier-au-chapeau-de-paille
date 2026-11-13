#!/usr/bin/env python3
"""Construit index.html à partir de source/texte.md.

Le moteur Harlowe (repris du site de Violette et Patate) est conservé tel quel dans index.html :
seules les pages et la feuille de style du livre sont régénérées.

Format de texte.md : la ligne en italique du début est la mention de fan fiction ; chaque chapitre commence
par « ## Chapitre n. Titre » ; « !chapitre-NN-carre.jpg » et « !chapitre-NN-A5.jpg » repèrent les images
(la carrée sert au site, l'A5 au livret) ; la consigne d'un tirage est une ligne en gras « **Lance le dé … :** »,
suivie de « - Un nombre pair : poursuis au chapitre n. » et « - Un nombre impair : … » ; un renvoi simple
s'écrit « - Poursuis au chapitre n. » ; un choix du lecteur « - S'il a reçu …, poursuis au chapitre n. » ;
« **FIN** » termine l'histoire.

Usage, depuis la racine du dépôt : python3 source/construire_site.py
"""
import html
import re
import uuid
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TEXTE = RACINE / "source" / "texte.md"
SORTIE = RACINE / "index.html"
NOINDEX = '<meta name="robots" content="noindex, nofollow, noarchive">'
# Favicon : le chapeau de paille de Kévine, découpé dans l'illustration du chapitre 1
FAVICON = ('<link rel="icon" type="image/png" sizes="48x48" href="images/favicon-48.png">'
           '<link rel="icon" type="image/png" sizes="180x180" href="images/favicon.png">'
           '<link rel="apple-touch-icon" href="images/favicon.png">')

TITRE = "Le fermier au chapeau de paille"
# Résumé de couverture écrit par Manon (13/11/2026), à garder mot pour mot
SYNOPSIS = ("Quand l’ombre d’un dragon condamne les récoltes de son village, Kévine, jeune fermier au chapeau de paille, "
            "part affronter l’inconnu avec Gertrude, sa fidèle renarde. Pour sauver les siens, il devra découvrir qu’un "
            "héros peut venir des champs.")
# Mention courte de la couverture ; la mention longue (début de texte.md) est sur la page de contexte
AVERTISSEMENT_COURT = ("Fan fiction librement inspirée du jeu vidéo Minecraft · "
                       "Ce livre n’est ni approuvé ni soutenu par Mojang Studios ou Microsoft.")
AUTEURS = "Antoine et Émile"

# Texte écrit par Manon le 03/11/2026, modèle commun aux livres de l'atelier ; seule la phrase sur le
# genre change d'un livre à l'autre
CONTEXTE = [
    "En octobre 2026, le L.A.B a animé l’atelier « La quête du curry, une histoire dont tu es le héros » "
    "dans les bibliothèques Méjanes d’Aix-en-Provence. Les enfants ont été accompagnés dans la création "
    "d’un récit complet, depuis l’invention des personnages jusqu’à la construction d’une intrigue "
    "reliant les différentes étapes de leur aventure.",
    "Nous leur avons proposé d’introduire une part de hasard dans leur récit. Le résultat d’un lancer de "
    "dé pouvait modifier le déroulement de certains passages et conduire le lecteur vers un chapitre ou "
    "un autre.",
    "Les enfants ont ainsi exploré, sans écran, des notions liées à la pensée computationnelle, une "
    "manière de décomposer un problème et d’organiser les étapes pour le résoudre. Ils ont formulé des "
    "règles de type « si… alors… », créé des embranchements et réfléchi à la façon dont les chemins se "
    "rejoignent pour former une histoire cohérente.",
    "Antoine et Émile ont choisi de situer leur aventure dans l’univers de Minecraft, un monde qu’ils "
    "connaissent par cœur, avec ses outils à fabriquer, ses créatures et ses mondes à traverser.",
    "L’atelier ne durant que deux heures, nous tenions à offrir à chaque enfant un livre complet "
    "pour illustrer leur travail et les rendre fiers de leurs productions. Le L.A.B a donc "
    "prolongé et mis en forme leur récit à l’aide d’outils numériques (l’intelligence "
    "artificielle a notamment permis d’aboutir à une histoire achevée et à un ensemble de visuels "
    "correspondant à leurs descriptions mais uniformes tout au long de la lecture).\n\n<b>À son "
    "origine, il y a avant tout les idées, les personnages et les dessins d’Antoine et d’Émile.</b>",
]

CSS = """
@font-face { font-family: "Pixelify Sans"; font-style: normal; font-weight: 400 700; font-display: swap; src: url("fonts/PixelifySans.woff2") format("woff2"); }
/* Les chiffres de Pixelify Sans se confondent avec des lettres (le 5 ressemble à un S) : les chiffres seuls
   viennent de Bricolage Grotesque très gras, choisi par Manon (essai F, 13/11/2026) */
@font-face { font-family: "Chiffres pixel"; font-weight: 400 800; font-display: swap; src: url("fonts/ChiffresBricolage.woff2") format("woff2"); unicode-range: U+30-39; }
@font-face { font-family: "Source Serif 4"; font-style: normal; font-weight: 400 700; font-display: swap; src: url("fonts/SourceSerif4.woff2") format("woff2"); }
@font-face { font-family: "Source Serif 4"; font-style: italic; font-weight: 400 700; font-display: swap; src: url("fonts/SourceSerif4-italique.woff2") format("woff2"); }

/* Ciel d'été (choisi par Manon le 13/11/2026) : page blanche, bandeau bleu ciel, texte et titres en noir,
   titres surlignés de jaune paille, numéro dans une étiquette bleue, encadré du dé bleu nuit à ombre jaune */
:root {
  --fond: #ffffff;
  --encre: #1a1a1a;
  --ciel: #3aa0e8;
  --nuit: #14507f;
  --nuit-clair: #eef8ff;
  --paille: #f7c531;
  --paille-clair: #ffd95c;
}
* { font-variant-ligatures: none; }
html, body, tw-story { background-color: var(--fond); color: var(--encre); }
/* Le bandeau bleu ciel en haut de chaque page */
tw-story { border-top: 14px solid var(--ciel); }
tw-story {
  font-family: "Source Serif 4", Georgia, serif;
  font-size: 1.08em;
  line-height: 1.65;
  padding: 3em 1.25em 4em;
  overflow: clip;
}
tw-sidebar { display: none; }
tw-passage { max-width: 1120px; margin: 0 auto; }

/* Pages de lecture : l'illustration à gauche (elle suit la lecture au défilement), le texte à droite */
/* Pages de lecture : la grande image à gauche, collée au bord de la fenêtre et sur toute sa hauteur, sans marge ;
   le texte à droite, avec le lien « ← Couverture » en tête */
tw-story:has(.page) { padding: 0; }
tw-passage:has(.page) { max-width: none; }
.page { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: clamp(1.5em, 4vw, 3.5em); align-items: start; }
.page .texte { max-width: 760px; padding: 2em clamp(1em, 3vw, 2.5em) 4em 0; }
.page.sans-image { grid-template-columns: minmax(0, 1fr); max-width: 680px; margin: 0 auto; }
/* L'image reste exactement là où elle apparaît (bandeau 14 px + marge haute de la page) : en lisant, elle ne
   remonte pas dans la marge, elle accompagne le texte */
.cote { position: sticky; top: 0; }
/* La grande image (A5, en hauteur) tient toujours dans la fenêtre */
.cote img { display: block; height: min(100vh, calc(52vw * 1.42)); width: auto; }

.chapitre { font-size: 1rem; margin: 0 0 1.1em; font-weight: 400; line-height: 1.05; display: flex; align-items: center; gap: 1em; }
.chapitre .entete { display: block; min-width: 0; }
.chapitre .miniature { flex: none; width: 92px; height: 92px; border-radius: 8px; box-shadow: 0 6px 14px -6px rgba(20, 80, 127, 0.6); }
.chapitre .numero { display: inline-block; font-family: "Chiffres pixel", "Pixelify Sans", monospace; font-weight: 600; font-size: 1.05rem; color: #fff; background: var(--ciel); padding: 0.1em 0.6em; border-radius: 3px; margin-bottom: 0.45em; }
.chapitre .titre { display: block; font-family: "Chiffres pixel", "Pixelify Sans", monospace; font-weight: 600; font-size: clamp(1.6rem, 3.2vw, 2.15rem); color: var(--encre); }
.chapitre .titre span { background: linear-gradient(transparent 62%, var(--paille) 62% 92%, transparent 92%); box-decoration-break: clone; -webkit-box-decoration-break: clone; }
.texte p, .texte { font-size: 1.04rem; }

.separateur { display: flex; align-items: center; justify-content: center; gap: 0.8em; margin: 1.6em 0 1.4em; }
.separateur .trait { width: 3.2em; height: 3px; background: var(--ciel); }
/* Les traits prennent la couleur de l'objet */
.separateur-diamant .trait { background: #3cc8d8; }
.separateur-flamme .trait { background: #f07a1a; }
.separateur-oeil .trait { background: #1f9a5c; }
.separateur .objet { width: 40px; height: 40px; object-fit: contain; display: block; }

/* Renvoi simple (choix A de Manon) : un lien en police pixel bleu nuit, centré sous le séparateur, suivi d'une petite
   flèche en pixels bleu ciel ; il se souligne au survol */
.elan { display: flex; justify-content: center; margin-top: 0.4em; }
.elan tw-link, .elan .enchantment-link {
  display: inline-flex; align-items: center; gap: 0.55em; font-family: "Chiffres pixel", "Pixelify Sans", monospace; font-weight: 600;
  font-size: 1.2rem; color: var(--nuit); text-decoration: none;
}
.elan tw-link::after, .elan .enchantment-link::after { content: ""; width: 22px; height: 22px; flex: none; background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8' shape-rendering='crispEdges'%3E%3Crect x='0' y='3' width='5' height='2' fill='%233aa0e8'/%3E%3Crect x='4' y='1' width='1' height='6' fill='%233aa0e8'/%3E%3Crect x='5' y='2' width='1' height='4' fill='%233aa0e8'/%3E%3Crect x='6' y='3' width='1' height='2' fill='%233aa0e8'/%3E%3C/svg%3E") center / contain no-repeat; }
.elan tw-link:hover, .elan .enchantment-link:hover { text-decoration: underline; text-underline-offset: 0.25em; }
tw-link, .enchantment-link { color: var(--nuit); font-weight: 600; text-decoration: none; }
/* Harlowe colore les liens déjà visités : ici, aucun lien ne change de couleur après un clic (demande de Manon) */
tw-link.visited, .enchantment-link.visited, tw-link.visited:hover { color: var(--nuit); }
/* « Commencer l’aventure » et « Poursuis » restent toujours dans le bleu nuit d'origine */
.elan tw-link.visited, .elan tw-link.visited:hover { color: var(--nuit); }
/* Les chapitres proposés par le dé, en noir, même déjà lus */
.tirage tw-link, .tirage .enchantment-link, .tirage tw-link.visited, .tirage tw-link:hover { color: var(--encre); }
tw-link:hover, .enchantment-link:hover { color: var(--nuit); text-decoration: underline; text-underline-offset: 0.2em; }

/* Encadré du dé : bordure bleu nuit et ombre pleine jaune paille ; à gauche, le chapeau de paille détouré
   (tiré de l'illustration A5 du chapitre 14, où il est entier), qu'on touche pour lancer le dé */
.de { border: 3px solid var(--nuit); box-shadow: 5px 5px 0 var(--paille); background: var(--nuit-clair); padding: 0.9em 1em; margin: 0.4em 5px 0 0; }
/* Le chapeau, entier et sans cadre, à droite de la consigne */
.de-tete { display: flex; gap: 0.9em; align-items: center; justify-content: space-between; }
.de-tete .consigne { order: 1; }
.de-tete .chapeau { order: 2; }
.chapeau {
  position: relative; flex: none; width: 128px; height: 74px; padding: 0; cursor: pointer; border: none; background-color: transparent;
  background: url("images/chapeau.png") center / contain no-repeat; filter: drop-shadow(0 4px 3px rgba(20, 80, 127, 0.35));
  transition: transform 0.15s ease;
}
.chapeau:hover { transform: translateY(-2px) rotate(-3deg); }
.chapeau.roule { animation: secoue 0.6s ease; }
@keyframes secoue { 20% { transform: rotate(-12deg); } 40% { transform: rotate(10deg); } 60% { transform: rotate(-6deg); } 80% { transform: rotate(4deg); } }
/* Le nombre tiré s'affiche sous le chapeau, centré, dans la police des titres et surligné de jaune paille */
.chapeau .face {
  position: absolute; left: 50%; top: 100%; transform: translateX(-50%); margin-top: 0.15em; display: none;
  font-family: "Chiffres pixel", "Pixelify Sans", monospace; font-weight: 700; font-size: 46px; line-height: 1.1; color: var(--encre);
  background: linear-gradient(transparent 62%, var(--paille) 62% 92%, transparent 92%); padding: 0 0.15em;
}
.chapeau.montre .face { display: block; }
.consigne b { display: block; font-family: "Chiffres pixel", "Pixelify Sans", monospace; font-weight: 600; font-size: 1.2rem; color: var(--encre); line-height: 1.15; }
.consigne span { display: block; font-size: 0.98rem; }
.resultat:empty { display: none; }
.resultat { display: block; font-style: italic; font-size: 0.95rem; color: var(--nuit); margin-top: 0.6em; }
.tirages { margin-top: 0.3em; }
.tirage { display: flex; align-items: baseline; gap: 0.7em; margin: 0.35em 0; }
.tirage b { font-family: "Chiffres pixel", "Pixelify Sans", monospace; font-weight: 600; font-size: 0.95rem; color: #fff; background: var(--nuit); padding: 0.05em 0.5em; min-width: 4.2em; text-align: center; }
/* Choix du lecteur (sans dé) : le même encadré, sans le chapeau */
.choix-lecteur .consigne b { margin-bottom: 0.4em; }
.choix-lecteur .option { display: block; margin: 0.45em 0; }

.mention { display: block; margin-top: 2.6em; font-size: 0.85rem; font-style: italic; color: #5c6670; }
.fin { text-align: center; margin-top: 1.4em; }
.mot-fin { display: block; font-family: "Chiffres pixel", "Pixelify Sans", monospace; font-weight: 700; font-size: 2.4rem; color: var(--encre); }
.secondaires { display: flex; flex-wrap: wrap; justify-content: center; gap: 0.4em 1.4em; margin-top: 0.8em; font-size: 0.98rem; }

/* Page de garde : l'image à gauche, le titre à droite, le tout tient dans l'écran */
/* Tout tient dans la hauteur de la fenêtre : marges de la page réduites, tailles calculées sur la hauteur */
tw-story:has(.garde) { padding: 0; }
tw-passage:has(.garde) { max-width: none; }
/* Comme les chapitres : l'image collée au bord gauche, sur toute la hauteur, sans marge ni recadrage */
.garde { display: flex; align-items: center; gap: clamp(1.5em, 4vw, 3.5em); height: calc(100vh - 14px); box-sizing: border-box; padding: 0 clamp(1em, 3vw, 2.5em) 0 0; }
/* Couverture recadrée en carré (Manon, 13/11/2026 : « qu'elle prenne plus de place ») */
.garde-image { display: block; flex: none; width: min(calc(100vh - 14px), 62vw); height: auto; aspect-ratio: 1; align-self: flex-start; }
.garde-texte { max-width: 30em; }
.surtitre { display: block; font-style: italic; font-size: clamp(0.85rem, 2vh, 1.05rem); color: #5c6670; }
.garde-titre { font-family: "Chiffres pixel", "Pixelify Sans", monospace; font-weight: 600; font-size: clamp(1.6rem, min(4vw, 6vh), 3.3rem); line-height: 1.12; margin: 0.2em 0 0.3em; }
.garde-titre span { background: linear-gradient(transparent 62%, var(--paille) 62% 92%, transparent 92%); box-decoration-break: clone; -webkit-box-decoration-break: clone; }
.noms { display: block; font-size: clamp(1rem, 2.6vh, 1.25rem); }
.resume { display: block; margin-top: 0.9em; font-size: clamp(0.92rem, 2.3vh, 1.1rem); line-height: 1.55; }
.commencer { justify-content: flex-start; margin-top: clamp(0.6em, 2.5vh, 1.6em); }
.commencer tw-link, .commencer .enchantment-link { font-size: clamp(1.2rem, 3.4vh, 1.55rem); }
.garde .mention { margin-top: clamp(0.8em, 2.5vh, 1.8em); font-size: clamp(0.72rem, 1.7vh, 0.85rem); }
@media (max-width: 820px) {
  tw-story:has(.garde) { padding: 1.4em 1em 3em; }
  .garde { flex-direction: column; gap: 1.4em; height: auto; padding: 0; }
  .garde-image { width: 100%; max-width: 480px; }
}

/* Liens secondaires de la page de garde et lien de retour à la couverture en haut des chapitres */
.garde .secondaires { justify-content: flex-start; margin-top: clamp(0.5em, 1.6vh, 1.1em); }
.retour { display: block; margin: 0 0 1.4em; line-height: 1.6; }
.retour tw-link, .retour .enchantment-link { font-size: 0.95rem; }
.retour tw-link::before, .retour .enchantment-link::before { content: "← "; }

/* Pages annexes */
.lien-retour { display: block; margin-bottom: 1.4em; font-size: 0.95rem; }
.lien-retour tw-link::before { content: "← "; }
/* Page « Comment est née cette histoire » (modèle commun aux livres de l'atelier) */
.contexte { max-width: 1000px; margin: 0 auto; text-align: center; }
.contexte .lien-retour { text-align: left; }
.contexte h1 span { background: linear-gradient(transparent 62%, var(--paille) 62% 92%, transparent 92%); }
.contexte-texte { max-width: 38em; margin: 0 auto; }
.portraits { display: flex; justify-content: center; align-items: flex-end; gap: 3em; margin: 0.5em 0 0.6em; }
.portraits figure { margin: 0; }
.portraits img { display: block; height: 9em; width: auto; margin: 0 auto; }
.portraits figure:nth-child(2) img { height: 5em; }  /* Gertrude est plus petite que Kévine */
.portraits figcaption { font-family: "Chiffres pixel", "Pixelify Sans", monospace; font-weight: 600; color: var(--nuit); margin-top: 0.3em; }
.citation { max-width: 30em; margin: 1.8em auto; font-family: "Chiffres pixel", "Pixelify Sans", monospace; font-weight: 600; font-size: 1.4em; line-height: 1.35; color: var(--nuit); }
.citation .source { display: block; margin-top: 0.5em; font-family: "Source Serif 4", serif; font-weight: 400; font-style: italic; font-size: 0.6em; color: #5c6670; }
.table-fiches { margin: 2.4em auto 0; padding: 1.6em 1.5em; background: var(--nuit-clair); border: 3px solid var(--nuit); box-shadow: 5px 5px 0 var(--paille); }
.titre-table { display: block; font-family: "Chiffres pixel", "Pixelify Sans", monospace; font-weight: 600; font-size: 1.3em; margin-bottom: 1.1em; }
.miniatures { display: flex; justify-content: center; align-items: flex-start; flex-wrap: wrap; gap: 1.8em; }
.miniatures figure { margin: 0; }
.miniatures figcaption { margin-top: 0.7em; font-style: italic; color: #5c6670; }
.miniature { display: block; padding: 0; border: none; background: none; cursor: zoom-in; }
.miniature img { display: block; height: 13em; width: auto; box-shadow: 0 4px 14px rgba(20, 80, 127, 0.3); transition: transform 0.2s ease; }
.miniatures figure:nth-child(1) img { transform: rotate(-2deg); }
.miniatures figure:nth-child(3) img { transform: rotate(2deg); }
.miniature:hover img { transform: rotate(0) scale(1.04); }
.contexte .credits { margin-top: 1.6em; color: #5c6670; }
.contexte .secondaires { justify-content: center; margin-top: 1.2em; }
/* Fiche ouverte en grand par-dessus la page ; un clic ou Échap la referme */
.agrandi { position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center; padding: 2vh 2vw; background: rgba(20, 50, 80, 0.85); cursor: zoom-out; }
.agrandi img { max-width: 100%; max-height: 96vh; box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4); }
@media (max-width: 600px) { .portraits img { height: 6em; } .miniature img { height: 10em; } }
.contexte h1, .arbre h1 { font-family: "Chiffres pixel", "Pixelify Sans", monospace; font-weight: 600; font-size: clamp(1.6rem, 3.2vw, 2.1rem); color: var(--encre); margin: 0 0 0.6em; line-height: 1.1; }
.credits { display: block; margin-top: 1.6em; font-size: 0.9rem; font-style: italic; white-space: pre-line; }
.arbre { text-align: center; }
.arbre img { display: block; width: 100%; max-width: 900px; margin: 1em auto 0; }

@media (max-width: 820px) {
  tw-story { padding: 1.4em 1em 3em; }
  .page { grid-template-columns: minmax(0, 1fr); gap: 1.2em; }
  .page .texte { padding: 0 1em 3em; }
  .cote img { width: 100%; height: auto; }
  .cote { position: relative; top: auto; }
}
"""


def e(texte):
    return html.escape(texte, quote=True)


def lire_mention():
    debut = TEXTE.read_text(encoding="utf-8").split("\n## ", 1)[0].strip()
    return debut.strip("*").strip()


def lire_chapitres():
    blocs = re.split(r"^## ", TEXTE.read_text(encoding="utf-8"), flags=re.M)[1:]
    chapitres = []
    for bloc in blocs:
        lignes = bloc.strip().split("\n")
        numero, titre = lignes[0].strip().split(". ", 1)
        paragraphes = [p.strip() for p in "\n".join(lignes[1:]).split("\n\n") if p.strip()]
        chapitres.append({"nom": numero, "numero": numero, "titre": titre, "paragraphes": paragraphes})
    return chapitres


RENVOI = re.compile(r"(.*?)[,:]?\s*[Pp]oursuis au chapitre (\d+)\.?$")


def lire_choix(ch):
    """Sépare le récit, la consigne, les tirages (pair/impair), les choix du lecteur, le renvoi et la fin."""
    corps, consigne, tirages, options, renvoi, fin = [], None, [], [], None, False
    for p in ch["paragraphes"]:
        if p.startswith("!"):
            continue                                   # repères d'images (site et livret)
        if p == "**FIN**":
            fin = True
        elif p.startswith("**") and p.endswith("**"):
            consigne = p[2:-2].strip().rstrip(" :").strip()
        elif p.startswith("- "):
            for ligne in p.split("\n"):
                m = RENVOI.match(ligne[2:].strip())
                assert m, f"Choix illisible dans {ch['nom']} : {ligne}"
                libelle, cible = m.group(1).strip(), int(m.group(2))
                if libelle.startswith("Un nombre pair"):
                    tirages.append(("Pair", cible))
                elif libelle.startswith("Un nombre impair"):
                    tirages.append(("Impair", cible))
                elif libelle:
                    options.append((libelle, cible))
                else:
                    renvoi = cible
        else:
            corps.append(p)
    if tirages:
        assert [t[0] for t in tirages] == ["Pair", "Impair"], f"Tirage incomplet dans {ch['nom']}"
    return corps, consigne, tirages, options, renvoi, fin


# Séparateurs : un objet en voxel dessiné par Manon (diamant, flamme, œil), entre deux traits de sa couleur.


RANGS = {}


def rangs_de_lecture():
    """Rang de chaque chapitre dans l'arbre (une ligne de plus que son prédécesseur le plus bas) : tout chemin de
    lecture passe d'un rang au suivant, donc l'objet change à chaque chapitre, quel que soit le parcours."""
    if not RANGS:
        aretes = []
        for ch in lire_chapitres():
            _, _, tirages, options, renvoi, _ = lire_choix(ch)
            a = 0 if ch["nom"] == "Prologue" else int(ch["nom"].split()[-1])
            aretes += [(a, n) for _, n in tirages] + [(a, n) for _, n in options] + ([(a, renvoi)] if renvoi else [])
        RANGS[0] = 0
        for n in sorted({b for _, b in aretes}):
            RANGS[n] = max(RANGS[a] for a, b in aretes if b == n) + 1
    return RANGS


def objet_du_chapitre(cle):
    """Le diamant, la flamme et l'œil alternent strictement le long de la lecture (choix de Manon, 13/11/2026)."""
    return ("diamant", "flamme", "oeil")[rangs_de_lecture()[cle] % 3]


def separateur(objet):
    # Les objets en voxel dessinés par Manon (images/objets/, originaux dans Sources/Objets)
    return (f'<div class="separateur separateur-{objet}"><span class="trait"></span>'
            f'<img class="objet" src="images/objets/{objet}.png" alt=""><span class="trait"></span></div>')


SEPARATEUR = separateur("diamant")

# Le chapeau tient lieu de dé : on le touche, il se secoue et montre un nombre de 1 à 6 (pair et impair
# ont la même probabilité). Il ne choisit jamais à la place du lecteur, qui suit ensuite le bon renvoi.
SCRIPT = """
// Page de contexte : une fiche s'ouvre en grand, un clic referme
document.addEventListener('click', function (evenement) {
  var ouvert = document.querySelector('.agrandi');
  if (ouvert) { ouvert.remove(); return; }
  var miniature = evenement.target.closest('.miniature');
  if (!miniature) return;
  var fond = document.createElement('div');
  fond.className = 'agrandi';
  var image = document.createElement('img');
  image.src = miniature.querySelector('img').src;
  image.alt = miniature.querySelector('img').alt;
  fond.appendChild(image);
  document.body.appendChild(fond);
});
document.addEventListener('keydown', function (evenement) {
  var ouvert = document.querySelector('.agrandi');
  if (ouvert && evenement.key === 'Escape') ouvert.remove();
});
document.addEventListener('click', function (evenement) {
  var chapeau = evenement.target.closest('.chapeau');
  if (!chapeau || chapeau.classList.contains('roule')) return;
  var resultat = chapeau.closest('.de').querySelector('.resultat');
  var face = 1 + Math.floor(Math.random() * 6);
  chapeau.classList.remove('montre');
  chapeau.classList.add('roule');
  resultat.textContent = '';
  setTimeout(function () {
    chapeau.classList.remove('roule');
    chapeau.querySelector('.face').textContent = face;
    chapeau.classList.add('montre');
  }, 620);
});
"""


def lien(texte, cible):
    return f"[[{texte}->{cible}]]"


def nom_passage(n):
    return f"Chapitre {n}"


def illustration(nom):
    return "prologue" if nom == "Prologue" else f"chapitre-{int(nom.split()[-1]):02d}"


def passage_chapitre(ch, mention):
    corps, consigne, tirages, options, renvoi, fin = lire_choix(ch)
    cle = 0 if ch["nom"] == "Prologue" else int(ch["nom"].split()[-1])
    objet = objet_du_chapitre(cle)
    suite = [separateur(objet)]
    if tirages:
        # En ligne, on ne lance pas de dé : on touche le chapeau (le livret garde « Lance le dé »)
        assert consigne.startswith("Lance le dé"), f"Consigne inattendue dans {ch['nom']} : {consigne}"
        reste = consigne[len("Lance le dé"):].strip()
        lignes = "".join(f'<span class="tirage"><b>{d}</b><span>{lien(nom_passage(n), nom_passage(n))}</span></span>'
                         for d, n in tirages)
        suite.append('<div class="de"><div class="de-tete">'
                     '<button class="chapeau" type="button" aria-label="Toucher le chapeau pour lancer le dé">'
                     '<span class="face"></span></button>'
                     f'<span class="consigne"><b>Touche le chapeau</b><span>{reste}</span></span></div>'
                     f'<span class="resultat" aria-live="polite"></span><div class="tirages">{lignes}</div></div>')
    elif options:
        lignes = "".join(f'<span class="option">{lien(libelle + ", poursuis au chapitre " + str(n), nom_passage(n))}</span>'
                         for libelle, n in options)
        suite.append(f'<div class="de choix-lecteur"><span class="consigne"><b>{consigne}</b></span>{lignes}</div>')
    elif renvoi:
        suite.append(f'<div class="elan">{lien(f"Poursuis au chapitre {renvoi}", nom_passage(renvoi))}</div>')
    if fin:
        suite = [separateur(objet), '<div class="fin"><span class="mot-fin">Fin</span><div class="secondaires">'
                 f'{lien("Comment est née cette histoire", "Comment est née cette histoire")}'
                 f'{lien("L’arbre de l’histoire", "L’arbre de l’histoire")}'
                 f'{lien("Relire depuis le début", "Prologue")}</div></div>']
    numero = f'<span class="numero">{ch["numero"]}</span>'
    # Deux images par chapitre : la miniature carrée à côté du numéro et du titre, la grande image A5 à côté du texte
    miniature = RACINE / f"images/miniatures/{illustration(ch['nom'])}.jpg"
    vignette = (f'<img class="miniature" src="images/miniatures/{miniature.name}" alt="">' if miniature.exists() else "")
    retour = f'<span class="retour">{lien("Couverture", "Couverture")}</span>'
    texte = (f'<div class="texte">{retour}<h1 class="chapitre">{vignette}<span class="entete">{numero}'
             f'<span class="titre"><span>{ch["titre"]}</span></span></span></h1>'
             + "\n\n".join(corps) + "".join(suite) + "</div>")
    image = RACINE / f"images/grandes/{illustration(ch['nom'])}.jpg"
    if image.exists():
        cote = f'<div class="cote"><img src="images/grandes/{image.name}" alt="{e(ch["titre"])}"></div>'
        return f'<div class="page">{cote}{texte}</div>'
    return f'<div class="page sans-image">{texte}</div>'


def passage_garde(mention):
    """Page de garde : l'image de couverture de Manon à gauche, le titre et le bouton à droite, sans défilement."""
    return ('<div class="garde"><img class="garde-image" src="images/couverture.jpg" alt="">'
            '<div class="garde-texte"><span class="surtitre">Une histoire dont le lecteur est le héros</span>'
            f'<h1 class="garde-titre"><span>{TITRE}</span></h1><span class="noms">{AUTEURS}</span>'
            f'<span class="resume">{SYNOPSIS}</span>'
            f'<div class="elan commencer">{lien("Commencer l’aventure", "Prologue")}</div>'
            f'<div class="secondaires">{lien("Comment est née cette histoire", "Comment est née cette histoire")}'
            f'{lien("L’arbre de l’histoire", "L’arbre de l’histoire")}</div>'
            f'<span class="mention">{AVERTISSEMENT_COURT}</span></div></div>')


# Une phrase de leur fiche récit, à peine remise au propre
CITATION = "Son frère arrive et lui dit qu’un fermier ne pourra jamais sauver le monde !"


def miniature(fichier, legende, description):
    return (f'<figure><button class="miniature" type="button" aria-label="Agrandir {description}">'
            f'<img src="images/fiches/{fichier}" alt="{description}"></button>'
            f'<figcaption>{legende}</figcaption></figure>')


def portrait(fichier, nom):
    return (f'<figure><img src="images/dessins/{fichier}" alt="{nom}, dessiné par Antoine et Émile">'
            f'<figcaption>{nom}</figcaption></figure>')


def passage_contexte(mention):
    """Modèle commun : dessins des enfants détourés, titre, séparateur, texte centré, une phrase de leur fiche
    récit, les fiches de l'atelier en miniatures cliquables, les crédits et la mention longue."""
    return (
        f'<div class="contexte"><span class="lien-retour">{lien("Couverture", "Couverture")}</span>'
        '<div class="portraits">' + portrait("kevine.png", "Kévine") + portrait("gertrude.png", "Gertrude") + '</div>'
        f'<h1><span>Comment est née cette histoire</span></h1>{SEPARATEUR}'
        '<div class="contexte-texte">' + "\n\n".join(CONTEXTE[:4])
        + f'<div class="citation">« {CITATION} »<span class="source">Antoine et Émile, sur leur fiche récit</span></div>'
        + CONTEXTE[4] + '</div>'
        '<div class="table-fiches"><span class="titre-table">Les fiches de l’atelier</span><div class="miniatures">'
        + miniature("fiche_recit.jpg", "Le récit", "la fiche récit, par Antoine et Émile")
        + miniature("fiche_personnage_kevine.jpg", "Une fiche personnage", "la fiche personnage de Kévine")
        + miniature("fiche_situation_1.jpg", "Une fiche à embranchement", "la fiche situation n° 1, avec ses choix au dé")
        + '</div></div>'
        '<span class="credits">Une histoire librement inspirée du récit d’Antoine et d’Émile.\nRéalisation du livre : '
        "Laboratoire d’Aix-périmentation et de Bidouille.</span>"
        f'<span class="mention">{mention}</span>'
        f'<div class="secondaires">{lien("Commencer le livre", "Prologue")}</div></div>'
    )


def passage_arbre():
    return (
        f'<div class="arbre"><span class="lien-retour">{lien("Retour au début", "Couverture")}</span>'
        f'<h1>L’arbre de l’histoire</h1><img src="images/arbre.svg" alt="Tous les chemins de l’histoire"></div>'
    )


def construire():
    modele = SORTIE.read_text(encoding="utf-8")
    debut = modele[: modele.index("<tw-storydata")]
    moteur = modele[modele.index("</tw-storydata>"):]
    if NOINDEX not in debut:
        debut = debut.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + NOINDEX)
    debut = re.sub(r"<link rel=\"(?:icon|apple-touch-icon)\"[^>]*>", "", debut)
    debut = re.sub(r"\n{3,}", "\n", debut)
    debut = debut.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + FAVICON)
    debut = re.sub(r"<title>.*?</title>", f"<title>{TITRE}</title>", debut)
    debut = re.sub(r"JavaScript doit être activé pour lire [^.<]*\.", f"JavaScript doit être activé pour lire {TITRE}.", debut)
    moteur = re.sub(r"JavaScript doit être activé pour lire [^.<]*\.", f"JavaScript doit être activé pour lire {TITRE}.", moteur)

    mention = e(lire_mention())
    passages = [
        ("Couverture", "", passage_garde(mention)),
    ]
    for ch in lire_chapitres():
        passages.append((ch["nom"], "", passage_chapitre(ch, mention)))
    passages.append(("Comment est née cette histoire", "", passage_contexte(mention)))
    passages.append(("L’arbre de l’histoire", "", passage_arbre()))

    # Espaces insécables de la typographie française
    insecables = [("« ", "« "), (" »", " »"), (" :", " :"), (" ?", " ?"),
                  (" !", " !"), (" ;", " ;")]
    for i, (nom, tags, contenu) in enumerate(passages):
        for avant, apres in insecables:
            contenu = contenu.replace(avant, apres)
        passages[i] = (nom, tags, contenu)

    noms = {p[0] for p in passages}
    for nom, _, contenu in passages:
        for cible in re.findall(r"->([^\]]+)\]\]", contenu):
            assert cible in noms, f"Lien cassé dans {nom} : {cible}"
    assert "—" not in "".join(p[2] for p in passages) and "–" not in "".join(p[2] for p in passages)

    depart = 1 + [p[0] for p in passages].index("Couverture")
    xml = [f'<tw-storydata name="{e(TITRE)}" startnode="{depart}" creator="Twine" creator-version="2.12.1" '
           f'format="Harlowe" format-version="3.3.9" ifid="{str(uuid.uuid5(uuid.NAMESPACE_URL, TITRE)).upper()}" '
           'options="" tags="" zoom="1" hidden>',
           f'<style role="stylesheet" id="twine-user-stylesheet" type="text/twine-css">{CSS}</style>',
           '<script role="script" id="twine-user-script" type="text/twine-javascript">' + SCRIPT + '</script>']
    for pid, (nom, tags, contenu) in enumerate(passages, start=1):
        xml.append(f'<tw-passagedata pid="{pid}" name="{e(nom)}" tags="{tags}" '
                   f'position="{pid * 150},0" size="100,100">{e(contenu)}</tw-passagedata>')
    SORTIE.write_text(debut + "".join(xml) + moteur, encoding="utf-8")
    print(f"{SORTIE} : {len(passages)} passages")


if __name__ == "__main__":
    construire()

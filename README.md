# Le fermier au chapeau de paille

Une histoire dont le lecteur est le héros, imaginée par Antoine et Émile pendant l'atelier « La quête du curry, une histoire dont tu es le héros » du L.A.B, à la bibliothèque des Deux Ormes (bibliothèques Méjanes, Aix-en-Provence), le 27 octobre 2026.

Une aventure librement inspirée de l'univers du jeu vidéo Minecraft. Ce livre n'est ni approuvé ni soutenu par Mojang Studios ou Microsoft. Minecraft est une marque de son propriétaire.

Le site n'est pas référencé par les moteurs de recherche.

## Modifier le livre

Le texte se trouve dans `source/texte.md`. Chaque chapitre commence par `## Chapitre n. Titre`. Un renvoi s'écrit `- Poursuis au chapitre n.`, un tirage `**Lance le dé … :**` suivi de `- Un nombre pair : poursuis au chapitre n.` et `- Un nombre impair : poursuis au chapitre n.`, un choix du lecteur `- S'il a reçu …, poursuis au chapitre n.`, et la fin `**FIN**`. Les lignes `!chapitre-NN-carre.jpg` et `!chapitre-NN-A5.jpg` repèrent les images : la carrée sert au site (`images/chapitres/chapitre-NN.jpg`), l'A5 au livret.

En ligne, le dé est remplacé par le chapeau de paille : on le touche, il montre un nombre de 1 à 6, et le lecteur suit le renvoi pair ou impair.

Après une modification, reconstruire la page et l'arbre :

```
python3 source/construire_site.py
python3 source/construire_arbre.py
```

Réalisation du livre : L.A.B, Laboratoire d'Aix-périmentation et de Bidouille.

---
name: reseau-fond
description: >-
  Pose l'adressage IP, les masques, les routes, les passerelles et le DNS avant NetPractice. Use when a packet path, subnet, gateway, mask or route is unclear, or when tempted to guess.
---

# Réseau de fond

Le sujet ou le schéma décide des adresses. Cette fiche décide de la méthode.

## Ordre

1. Lister chaque lien et les machines qui y sont branchées.
2. Donner à chaque lien un réseau : adresse réseau, masque, plage d'hôtes.
3. Vérifier que deux liens ne se recouvrent pas.
4. Écrire d'abord les routes connectées, puis les routes précises, puis la route par défaut.
5. Vérifier que chaque passerelle est une adresse d'hôte du lien d'à côté, pas l'adresse réseau, pas le broadcast.

## Masque

Un masque `/n` laisse `32 - n` bits pour le réseau local.

L'adresse réseau est l'adresse AND le masque. Le broadcast est l'adresse OR l'inverse du masque. Les hôtes sont entre les deux.

Deux machines se parlent sans routeur si leur adresse AND masque donne le même réseau.

Un masque trop large colle deux salles dans le même réseau. Un masque trop étroit sort une machine de son lien.

## Route

La table choisit la route dont le préfixe est le plus long et contient la destination.

`0.0.0.0/0` ne gagne que si aucune route plus précise ne convient.

Une route connectée n'a pas de passerelle. Une route vers un autre réseau a une passerelle, et cette passerelle doit être joignable par une route connectée.

La machine n'utilise pas sa propre adresse comme passerelle.

## DNS et NAT

Le DNS traduit un nom en adresse. Il ne choisit pas le chemin.

Le NAT traduit une adresse privée en adresse publique au bord du réseau. Derrière le NAT, les machines gardent leurs adresses privées. La route par défaut des machines privées pointe vers le routeur qui fait le NAT.

## Pièges

- Passerelle hors du sous-réseau de l'interface.
- Deux interfaces du même routeur dans le même réseau.
- Oublier la route retour. Un ping part, la réponse ne revient pas.
- Confondre l'adresse du routeur côté A et côté B.
- Mettre un masque d'hôte `/32` sur un lien qui doit porter plusieurs machines.

## Vérifier

Pour une destination, écrire les trois lignes : réseau de départ, route choisie, prochain saut. Recommencer depuis l'autre bout pour la réponse.

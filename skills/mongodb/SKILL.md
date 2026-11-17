---
name: mongodb
description: >-
  Schéma, index, requêtes et sécurité MongoDB (Node, Mongoose, mongosh). Use when designing a collection, writing find/aggregate, adding an index, reading explain() or passing user input to a query.
---

# MongoDB

Le brief et les écrans décident des données. Cette fiche décide de la méthode.

## Local

MongoDB tourne en espace utilisateur et reste arrêté par défaut
(voir `~/.agents/memory/machine/databases.md`).

- Démarrer : `mongod --config ~/.config/mongod.conf --fork`
- Arrêter à la fin de la tâche : `mongod --config ~/.config/mongod.conf --shutdown`
- Écoute seulement sur `127.0.0.1:27017`. Ne pas l'ouvrir sur `0.0.0.0`.

## Schéma

1. Partir des lectures : quelle page lit quoi, et combien de fois.
2. Imbriquer ce qui se lit toujours avec le parent et reste petit
   (adresse d'un user, lignes d'une commande).
3. Référencer par `_id` ce qui grossit sans limite ou se partage
   (commentaires d'un post, produits d'un catalogue).
4. Un document ne dépasse pas 16 Mo : un tableau qui grandit sans fin
   est une collection à part.
5. Valider à l'écriture : schéma Mongoose (`required`, `enum`, `min`) ou
   `$jsonSchema` sur la collection.

## Index

- Chaque requête fréquente a son index. `_id` est déjà indexé.
- Index composé dans l'ordre Égalité, Tri, Plage (règle ESR).
- `unique: true` pour un email ou un slug, pas un contrôle en JS avant insert.
- Vérifier avec `explain("executionStats")` : chercher `IXSCAN`, pas
  `COLLSCAN`, et `totalDocsExamined` proche de `nReturned`.

## Requêtes

- Projeter les champs utiles, jamais le mot de passe haché vers le client.
- Paginer par `_id` ou par date (`{ _id: { $gt: dernierId } }` + `limit`)
  plutôt que par `skip` sur une grosse collection.
- `aggregate` : `$match` et `$project` en premier pour réduire le flux.
- Écriture sur plusieurs documents liés : transaction (replica set requis),
  sinon revoir le schéma pour que ce soit un seul document.

## Sécurité

- Injection d'opérateurs : `req.body.email` peut valoir `{ "$ne": null }`.
  Forcer le type (`String(x)`, validation zod ou Joi) avant la requête, ou
  `mongoose.set('sanitizeFilter', true)`.
- Jamais `$where`, `$function` ni `$accumulator` avec une entrée utilisateur.
- Filtrer par propriétaire (`{ _id, owner: req.user.id }`) pour éviter l'IDOR.
- URI de connexion dans `.env`, jamais dans le code ni le dépôt.
- Utilisateur applicatif avec le rôle `readWrite` sur sa base, pas `root`.

## Vérifier

Pour chaque route touchée : la requête exacte, l'index utilisé
(`explain`), et le cas où l'entrée est un objet au lieu d'une chaîne.

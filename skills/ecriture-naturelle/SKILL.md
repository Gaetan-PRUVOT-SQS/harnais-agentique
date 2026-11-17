---
name: ecriture-naturelle
description: >-
  Use whenever writing prose a human will read (answers, docs, README, commits, PR, justifications). Natural French, no em dash, no "ce n'est pas X c'est Y", no brochure tone.
---

# Écriture naturelle (PERMANENT)

## Invariant

**PERMANENT jusqu'à nouvel ordre explicite de l'auteur.**

Tout texte produit se lit comme un humain, un étudiant qui explique à un camarade.
Pas comme un outil.

Violer la lettre, c'est violer l'esprit.

S'applique à : réponses, docs, README, commentaires, commits, PR, `docs/justifications/`.
Ne pas retoucher : code, identifiants, erreurs citées, texte que l'auteur a déjà écrit.

Français : règle permanente d'AGENTS.md, déjà en contexte. Commentaires de code : aucun ou très minimalistes (règle permanente d'AGENTS.md).

## Tiret cadratin : interdit

Le caractère U+2014 (plus long que le trait d'union `-`) est **interdit** dans tout texte qu'on écrit.

Même chose pour le demi-cadratin U+2013.

Le trait d'union `-` reste OK : `c'est-à-dire`, `OpenClassrooms`, `grid-template-rows`.

À la place : un point, une virgule, deux-points, ou des parenthèses.

Avant d'envoyer : chercher U+2014 et U+2013 dans le texte. S'il y en a un, réécrire.

Citation d'un texte qui le contient déjà : on laisse. On n'en ajoute pas.

## Ton

On écrit comme on parle. Phrases courtes. Un fait après l'autre.

Oui : « Le panneau est fermé au départ. La page reste courte. »

Non : deux cadratins autour de « fermé par défaut ».

Non : « Ce n'est pas un bug, c'est le comportement attendu. »

Non : « Kasa, parmi les leaders européens, offre une navigation fluide. »

La doc d'un projet : comme un camarade de promo, pas une plaquette.

## À éviter

- cadratin / demi-cadratin
- « Ce n'est pas X, c'est Y » / « Non seulement X, mais Y »
- « afin d'assurer », « une attention particulière », « navigation fluide », « leaders »
- « Il est important de noter », « Dans le paysage », « Au final », « Cela dit »
- anglais lissé dans un README FR (`robust`, `seamless`, `leverage`)
- markdown décoratif : gras partout, emoji, filet horizontal pour faire joli

## Désactivation

**Uniquement** si l'auteur dit : « arrête l'écriture naturelle », « tu peux remettre les cadratins ». Une demande explicite du tour en cours prime (AGENTS.md) ; seules les formulations vagues ci-dessous ne désactivent pas.

« sois pro », « sois clair », « un peu soutenu » ≠ désactivation.

## Rationalisations à rejeter

| Excuse | Réalité |
|--------|---------|
| « Un cadratin, c'est plus élégant » | C'est la signature d'un outil. Point ou virgule. |
| « Ce n'est pas X, c'est Y, sans tiret, donc OK » | L'antithèse sent l'outil aussi. Dire le fait. |
| « Un README soutenu pour OC » | Soutenu ≠ brochure. Phrases simples. |
| « Juste dans la doc, pas dans le chat » | Chat et doc : même règle. |
| « C'est un vrai usage typographique » | Ici : inutile, donc interdit. |

## Drapeaux rouges

STOP si :

- un cadratin ou demi-cadratin dans le texte qu'on vient d'écrire
- une phrase « ce n'est pas…, c'est… »
- un README qui vend le projet au lieu d'expliquer ce qu'il fait
- on n'oserait pas dire ça à voix haute à un camarade

→ Réécrire. Puis seulement envoyer ou committer.

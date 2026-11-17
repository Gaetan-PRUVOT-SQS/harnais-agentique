---
name: revenu-fixe
description: >-
  Courbe, bases de taux et DV01 par pilier. Use when building a discount curve, a swap, a bond or a swaption.
---

# Revenu fixe

Invariants : finance-quantitative. Un pricer de swaption ou de callable suit aussi pricing-derives et methodes-numeriques-finance.

## Courbe

Les instruments sont en ordre de maturité. Chacun est repris par la courbe au résidu près de zéro, ou l'optimiseur publie le résidu par instrument.

Ce qu'on interpole est un choix : log du discount, taux forward, spline. Un forward négatif ou un créneau, alors que les cotes sont lisses, se rejette. Si la cote de marché est elle-même ce créneau, on le dit.

Depuis le marché multi-courbes, la courbe d'actualisation et la courbe de projection sont deux objets. On actualise sur la courbe du RFR du collatéral (SOFR, €STR, SONIA). On projette chaque index sur sa courbe. Une courbe unique est un modèle de livre collatéralisé dans une seule devise, et ce choix est écrit. Un nouveau trade ne reconstruit pas une courbe LIBOR : l'index du contrat est celui qu'on projette.

Le test de courbe : les instruments de construction ressortent à leur prix de marché, et un instrument tenu hors du bootstrap (un swap d'une maturité non utilisée) sert de contrôle.

## Bases et calendriers

La base de jours est sur la confirmation. `ACT/360`, `ACT/365 Fixed`, `ACT/ACT ICMA` et `30/360` sont des familles. `30/360` a plusieurs variantes (américaine, européenne, ISDA) qui divergent en fin de mois. Le test nomme la variante.

Le calendrier de paiement est nommé : unadjusted, following, modified following, preceding, modified preceding, et la règle de fin de mois. Un samedi n'est pas une date de paiement quand le contrat est adjusted. Le test traverse un jour férié connu (Noël, Jour de l'an) et compare les dates à ce calendrier.

L'échéancier d'un swap se refait sur une confirmation connue, base et calendrier compris. On ne déduit pas la base de la seule devise.

## Prix cash

Le cash est le dirty (clean plus coupon couru) fois le nominal, à la date de règlement, avec le lag du marché. Le clean est la cote. Le yield est le taux qui retrouve ce prix à partir de l'échéancier. Deux obligations de même yield et de coupons différents n'ont pas le même risque.

Un OAS sans le modèle de taux qui l'a produit ne se compare pas à un autre OAS.

## Risque de courbe

On livre le DV01 par pilier, sur les piliers de la courbe, plus la convexité pour un grand mouvement. Un DV01 parallèle ou une duration modifiée masque un pivot de courbe.

## Swaptions

Près de zéro ou en taux négatifs, la quote est une vol normale (en points de base). Une vol lognormale Black n'a pas de sens sur un strike négatif, et explose près de zéro. Le test à vol normale nulle rend l'intrinsèque du taux forward du swap.

Le numéraire d'une swaption européenne est l'annuité. Le prix est l'annuité fois le Black ou le Bachelier du taux forward.

## Futures

On passe de la cote `100 - taux` au forward par l'ajustement de convexité. Le signe se vérifie dans le modèle choisi. Dans le cas usuel (Hull-White), le taux du future est au-dessus du forward simplement composé : on retire un ajustement positif pour retrouver le forward.

## Modèles de taux

Hull-White à un facteur colle à la courbe d'actualisation. Une vol et une force de rappel ne font pas un cube de swaptions. On écrit quels expiries et quels tenors sont tenus.

Libor market model : on calibre les caplets ou les swaptions, et on dit lesquels. Les deux à la fois, seulement avec l'écart publié. Le gel du drift est une approximation : une swaption européenne se vérifie en formule fermée dans la mesure terminale avant un callable.

## On s'arrête

- Une courbe qui ne reprend pas ses instruments de construction.
- Actualiser un SOFR collatéralisé sur une courbe d'un autre index, sans le dire.
- Un seul chiffre de duration pour un livre de swaps.
- Une vol lognormale sur un strike négatif.

## Références

- Les conventions de base et de calendrier se lisent sur la confirmation et sur le template ISDA de l'index, pas dans ce skill.
- Bâle MAR pour le capital de taux : skill risque-quantitatif.

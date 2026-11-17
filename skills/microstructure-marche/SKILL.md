---
name: microstructure-marche
description: >-
  Carnet, spread et prix exécutable. Use when backtesting fills, estimating market impact, or reading an order book.
---

# Microstructure

Invariants : finance-quantitative. La capacité et le compromis délai contre impact : portefeuille-quantitatif.

## Prix d'exécution

Le prix testé est le touch du côté pris, ou un modèle de remplissage écrit : probabilité, place dans la file, délai. Un backtest au mid suppose un remplissage gratuit.

Le spread paie le traitement de l'ordre, l'inventaire du market maker et la sélection adverse (Glosten et Milgrom, Journal of Financial Economics, 1985). Un flux qui choisit le sens après avoir vu un signal paie plus que le spread affiché.

## Impact

Le lambda de Kyle (Econometrica, 1985) est un modèle d'impact permanent linéaire. On l'estime sur le marché visé, ou on ne le met pas. La loi empirique en racine de la participation est dans portefeuille-quantitatif.

L'implementation shortfall (Perold, Journal of Portfolio Management, 1988) est l'écart entre le prix de décision et le prix réalisé, découpé en délai, mouvement de marché et frais. C'est la mesure d'une exécution.

## Horloge et carnet

L'horodatage est celui de l'échange. Une jointure quote-trade qui prend la quote de la même microseconde peut lire l'avenir. On prend la dernière quote strictement antérieure au trade.

Priorité de prix, puis de temps. Un remplissage simulé en bout de file est un autre modèle qu'un remplissage en tête. La place dans la file est une hypothèse écrite. Le volume affiché ignore la taille cachée (iceberg). Une stratégie qui croit voir toute la taille le dit.

Le tick, les enchères d'ouverture et de clôture, les haltes et les limites de prix cassent un modèle continu. Ces séances sont dans l'échantillon, ou exclues et nommées.

Le décalage de règlement (actions américaines au comptant : T+1 depuis le 28 mai 2024) est dans finance-quantitative. Le cash part à cette date, pas à l'horodatage du trade.

## On s'arrête

- Exécuter un backtest au mid.
- Joindre une quote contemporaine ou future au trade.
- Un lambda de Kyle collé sans estimation sur ce marché.
- Oublier les enchères et les haltes dans un échantillon intraday sans le dire.

## Références

- Glosten et Milgrom, Bid, ask and transaction prices in a specialist market, Journal of Financial Economics, 1985.
- Kyle, Continuous Auctions and Insider Trading, Econometrica, 1985.
- Perold, The Implementation Shortfall: Paper versus Reality, Journal of Portfolio Management, 1988.

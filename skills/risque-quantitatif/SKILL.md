---
name: risque-quantitatif
description: >-
  Expected shortfall, backtest, XVA et crédit. Use when measuring market or counterparty risk, or explaining a P&L.
---

# Risque quantitatif

Invariants et validation de modèle : finance-quantitative (SR 26-2). Un modèle de risque est un modèle au sens de cette lettre.

## Expected shortfall et VaR

La VaR est un quantile. Elle n'est pas sous-additive (Artzner, Delbaen, Eber, Heath, Mathematical Finance, 1999). Deux livres peuvent paraître plus sages séparés qu'ensemble, ou l'inverse. L'expected shortfall, moyenne de la queue au-delà du quantile, est cohérent pour une perte intégrable (Acerbi et Tasche, Journal of Banking and Finance, 2002).

Cadre de marché Bâle, MAR33, page lue le 2026-10-28. L'approche modèles internes calcule l'expected shortfall chaque jour, pour la banque et pour chaque desk. Niveau 97,5 %, unilatéral. Horizon de base 10 jours, puis horizons de liquidité 10, 20, 40, 60 et 120 par mise à l'échelle. Calibration sur une période de stress. Les facteurs non modélisables (NMRF) sont en capital à part, hors de cet expected shortfall. La note explicative de janvier 2019 dit qu'un expected shortfall à 97,5 % est du même ordre qu'une VaR à 99 % de Bâle 2.5, et qu'ils s'écartent quand la queue est épaisse.

Le backtest et le test d'attribution du P&L (PLA) sont dans MAR32. Le PLA compare le P&L théorique du modèle de risque au P&L hypothétique. Les bornes des zones se lisent dans le MAR32 en vigueur. On ne les fige pas ici.

## Quel calcul

La simulation historique prend la loi jointe empirique des chocs passés. Elle rate un choc absent de la fenêtre. Une fenêtre courte rate un régime. Une VaR gaussienne sous-estime une queue épaisse. L'historique filtré (chocs remis à l'échelle de la vol courante) répond mieux au regroupement des exceptions que l'historique brut. Le choix et la fenêtre sont écrits.

Le backtest publie le nombre d'exceptions et leur regroupement. Des exceptions en grappe disent que la dynamique de vol manque, même si le taux moyen d'exceptions a l'air tenu (Christoffersen, International Economic Review, 1998). Les seuils du feu de signalisation réglementaire se lisent dans MAR32.

## P&L expliqué

Le P&L du jour se décompose : delta, gamma, vega, thêta, trades nouveaux, inexpliqué. Un inexpliqué qui domine les risques expliqués veut dire que les facteurs sont incomplets, ou que les grecques viennent d'un autre modèle que celui qui marque le livre. Pour un desk au capital interne, c'est le sujet du PLA.

## XVA

Chaque lettre est un coût séparé, sur le netting set et le CSA réels.

- CVA : défaut de la contrepartie sur l'exposition positive non collatéralisée, perte en cas de défaut comprise.
- DVA : propre défaut sur l'exposition négative. Un écartement du propre crédit qui passe en produit se reporte à part du CVA. Ce produit ne finance pas la couverture.
- FVA : financement de la part non collatéralisée.
- ColVA : devise du collatéral, rémunération, seuils, montant minimum de transfert.
- MVA : financement de la marge initiale.
- KVA : coût du capital.

Un chiffre appelé CVA qui ignore le CSA, le netting set ou le wrong-way risk est une exposition incomplète, étiquetée comme telle. Wrong-way : la probabilité de défaut monte avec l'exposition (put vendu à la firme sous-jacente, change d'un pays émergent). Le CVA à défaut indépendant n'est alors pas le prix.

La convention de close-out (sortie en valeur sans risque, ou en valeur qui porte encore le risque de crédit) change le montant au défaut. Elle est nommée.

## Crédit

Forme réduite : une courbe de hasard se bootstrap sur les CDS, avec un recovery fixé. Changer le recovery déplace la courbe. Le recovery utilisé est écrit.

Forme structurelle (Merton) : l'action est un call sur les actifs. Utile pour un nom sans CDS. Le résultat dépend du levier et de la vol. Un spread de CDS demande une correspondance déjà testée.

Un spread « ISDA » reprend les hypothèses du modèle standard ISDA (recovery, conventions). On ne convertit pas un prix de CDS à la main.

Le DV01 de spread ne contient pas le saut au défaut. Un stress de défaut est à côté du risque de spread.

## Limites

Un livre a un jeu de limites : exposition, grecques, stress que la loi ne sait pas tirer (gap, décrochage, fermeture d'un marché), et une vue de liquidité (délai pour sortir). Une VaR à 99 % sur un jour ne tient pas lieu de ce jeu.

## On s'arrête

- Une limite de risque qui n'est qu'une VaR.
- Un expected shortfall réglementaire avec un seuil de PLA recopié de mémoire.
- Un CVA sans CSA ni netting set, présenté comme un prix.
- Un P&L du jour sans ligne inexpliquée.

## Références

- Artzner, Delbaen, Eber, Heath, Coherent Measures of Risk, Mathematical Finance, 1999.
- Acerbi et Tasche, On the coherence of expected shortfall, Journal of Banking and Finance, 2002.
- Christoffersen, Evaluating Interval Forecasts, International Economic Review, 1998.
- Bâle MAR33 : <https://www.bis.org/basel_framework/chapter/MAR/33.htm>
- Bâle MAR32 (backtest et PLA) : <https://www.bis.org/basel_framework/chapter/MAR/32.htm>

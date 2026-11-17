---
name: mlp-allocation
description: >-
  HRP, débruitage de covariance, allocation par grappes. Use when allocating from a large or noisy covariance.
---

# Allocation par grappes

Invariants : finance-quantitative. Coûts, rétrécissement, univers survivant : portefeuille-quantitatif. Borne de bruit d'une corrélation : ml4t-latent-factors. Un rendement espéré de facteur : mlp-causalite.

## Débruitage

On travaille sur la corrélation, pas sur la covariance brute. Les valeurs propres au-dessus du bord de bruit de Marchenko-Pastur restent. Celles du bruit sont remplacées par leur moyenne. On reconstruit, on ramène la diagonale à 1, puis on repasse en covariance avec les volatilités. L'estimation tient dans la fenêtre d'entraînement.

Avant de regrouper, on retire la composante de marché (la plus grande valeur propre) et on renormalise la diagonale à 1. Sinon le facteur de marché colle tous les titres dans la même grappe. López de Prado, Machine Learning for Asset Managers, Cambridge University Press, 2020. Le papier court est SSRN 3469961, 2019.

La borne numérique du bruit est celle de ml4t-latent-factors. Ici elle sert à clipper la matrice avant une allocation. Elle ne sert pas à extraire un facteur de prix.

## HRP

López de Prado, Building Diversified Portfolios that Outperform Out of Sample, Journal of Portfolio Management, 2016.

La distance entre i et j est √((1 - ρ_ij) / 2). On construit un arbre par regroupement hiérarchique. Le code du papier utilise la liaison simple. On réordonne la covariance selon les feuilles (forme quasi-diagonale).

La bisection récursive coupe cette liste en deux. Dans chaque moitié, les poids de départ sont en inverse de variance diagonale. La variance de la grappe est le quadrique de ces poids. Le capital se partage entre les deux moitiés en proportion inverse de ces variances. On descend jusqu'aux titres.

Cette allocation n'inverse pas la covariance entière et n'utilise pas de rendement espéré. Elle reste définie sur une covariance singulière. Le chapitre 16 du livre de 2018 reprend la construction, avec la liaison du plus proche voisin. Hors échantillon, on la compare à l'équipondéré et à une covariance rétrécie (portefeuille-quantitatif). Le papier de 2016 rapporte moins de variance hors échantillon que Markowitz sur les cas étudiés. Les écarts chiffrés du chapitre 16 sont ceux de son expérience. Ça ne se généralise pas sans cette comparaison.

## Allocation imbriquée

Après débruitage et retrait du marché : on alloue dans chaque grappe, on remplace la grappe par ce portefeuille, on alloue entre ces portefeuilles, on revient aux titres. Une erreur d'estimation reste dans sa grappe. C'est l'estimateur de la frontière dans SSRN 3469961.

Si un signal de rendement entre dans l'allocation, le graphe causal de ce signal est écrit avant (mlp-causalite). Débruiter la covariance ne répare pas un mauvais graphe.

## On s'arrête

- Inverser la covariance échantillon d'un grand univers.
- Donner des rendements espérés à HRP comme s'il les utilisait.
- Débruiter sur l'échantillon entier, fenêtre de test comprise.
- Regrouper sans retirer le marché quand un facteur commun domine.
- Prendre le HRP du papier de 2016 comme un classement définitif.

## Références

- López de Prado, Building Diversified Portfolios that Outperform Out of Sample, Journal of Portfolio Management, 2016.
- López de Prado, A Robust Estimator of the Efficient Frontier, SSRN 3469961, 2019.
- López de Prado, Machine Learning for Asset Managers, Cambridge University Press, 2020.
- López de Prado, Advances in Financial Machine Learning, Wiley, 2018, chapitre 16.

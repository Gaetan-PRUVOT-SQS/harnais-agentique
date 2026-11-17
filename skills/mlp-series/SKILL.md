---
name: mlp-series
description: >-
  Barres au volume et différenciation fractionnaire. Use when sampling bars or transforming a price before a model.
---

# Séries pour le machine learning de marché

Invariants : finance-quantitative. Fuite : ml4t-lookahead-bias. Séances : ml4t-calendar-ops. Ruptures, entropie et flux : mlp-traits.

López de Prado, Journal of Portfolio Management, 44(6), 2018, pièges 3 et 4. Les formules ci-dessous viennent de Advances in Financial Machine Learning, Wiley, 2018, chapitres 2 et 5.

## Barres

Une barre de temps prend trop d'heures creuses et pas assez l'ouverture. Les rendements qui en sortent sont plus autocorrélés et plus hétéroscédastiques (Easley, López de Prado et O'Hara, Journal of Portfolio Management, 2011).

On forme une barre quand un montant échangé est atteint, dans la devise du titre. Le seuil est fixe, ou il suit une grandeur déjà connue : capitalisation flottante, encours de dette. Un seuil qui utilise une capitalisation publiée plus tard est une fuite.

Les barres de ticks et de volume bougent avec le prix et le nombre de titres en circulation. On les garde si le montant échangé n'est pas la bonne horloge, et on le dit. Une enchère imprimée en un seul tick, et la fragmentation des ordres, cassent les barres de ticks. Clark (Econometrica, 1973) préférait déjà le volume au tick.

Le signe d'un trade, b_t, vaut le signe de la variation de prix si elle n'est pas nulle, sinon le signe précédent. b_t est dans {-1, 1}. Une barre reprend le dernier signe de la barre précédente.

Barre d'imbalance de ticks. θ_T est la somme des b_t. Sous l'information du départ, E0[θ_T] = E0[T] (2 P[b = 1] - 1). E0[T] est une moyenne mobile exponentielle des longueurs déjà closes. P[b = 1] est la même moyenne sur les signes déjà clos. La barre se ferme au plus petit T tel que |θ_T| ≥ E0[T] |2 P[b = 1] - 1|. Un flux informé ferme les barres plus souvent. L'horloge vise une information égale, pas un volume égal.

Barre d'imbalance de volume ou de notionnel. θ_T est la somme des b_t v_t. v est le nombre de contrats, ou le notionnel. E0[θ_T] = E0[T] (2 v+ - E0[v]), avec v+ = P[b = 1] E0[v | b = 1]. La barre se ferme quand |θ_T| ≥ E0[T] |2 v+ - E0[v]|. La taille bouge. Une opération sur titre n'impose pas un seuil fixe.

Barre de suites de ticks. θ_T est le max entre la somme des signes d'achat et l'opposé de la somme des signes de vente. On ne nette pas : la suite a le droit de se casser. L'espérance vaut E0[T] max{P[b = 1], 1 - P[b = 1]}. En volume ou en notionnel, le max porte sur les quantités signées, et l'espérance vaut E0[T] max{P[achat] E0[v | achat], P[vente] E0[v | vente]}.

## Événements

On n'étiquette pas chaque barre. Le filtre à somme cumulée est un échantillonnage, pas une règle de trading (Lam et Yam, Fama et Blume sont un autre usage). Les ruptures de structure sont dans mlp-traits.

Sur la différence de la série brute : S+ = max(0, S+ + différence), S- = min(0, S- + différence). On pose un événement quand S+ dépasse h, ou quand S- passe sous -h, puis on remet ce côté à zéro. Dans le livre, l'espérance à t - 1 est l'observation précédente. h est un multiple de volatilité passée, écrit avant. Un croisement de bande de Bollinger ne convient pas : rester autour de la bande déclenche trop souvent. Le filtre attend une excursion de longueur h.

## Panier et roll

Pour enchaîner des contrats, on suit un panier réinvesti K_t, avec K_0 = 1. Dividendes et portage sont dans K. Les coûts de rebalancement restent hors de K. Le bid-ask du panier virtuel est chargé à part. Le nombre d'unités négociables est limité par la jambe la moins active.

À un roll, si le nouveau contrat n'a pas encore de prix, on prend la prochaine ouverture. Les prix rollés servent au P&L. Les prix bruts servent à la taille et au capital. Sur un seul future, on cumule les écarts. L'alignement de fin se fait vers l'avant ou vers l'arrière, et on le dit. Des poids d'ACP mettent par défaut tout le risque sur la plus petite valeur propre. Un prix rollé peut devenir négatif. Le livre le montre sur le coton et le gaz naturel en contango. Ce sont des exemples, pas une liste close.

## Différenciation fractionnaire

L'ordre 1 donne un rendement stationnaire sans mémoire. Le niveau a la mémoire et une racine unitaire. L'ordre retenu est le plus petit d dans (0, 1) qui rejette cette racine au seuil écrit avant l'estimation.

Poids : ω_0 = 1, puis ω_k = -ω_{k-1} (d - k + 1) / k. Pour d = 1, on retrouve le rendement, et les poids passés d s'annulent. Pour d dans (0, 1), les poids après le premier sont dans (-1, 0).

Fenêtre qui s'allonge : chaque date a une mémoire de longueur différente. La perte de poids à partir du rang l est la somme des valeurs absolues des poids de l jusqu'à la fin, divisée par la somme de toutes les valeurs absolues. On jette le préfixe tant que cette perte dépasse τ. L'exemple du livre prend τ = 0,01. Cette fenêtre dérive encore vers le bas, parce que de nouveaux poids négatifs s'ajoutent.

Fenêtre de largeur fixe : on coupe dès que |ω_k| ≤ τ, et on réutilise le même vecteur. Plus de dérive. La loi n'est plus gaussienne, la série reste autocorrélée, et elle peut passer le test ADF. d* est le plus petit d de cette fenêtre qui passe l'ADF.

L'exemple du livre, E-mini, log-prix journaliers rollés : l'ADF des prix est proche de -0,34, celui des rendements proche de -46,9, le seuil à 95 % proche de -2,86. L'ADF passe vers d = 0,35, avec une corrélation encore proche de 0,995 avec la série d'origine. Les rendements corrèlent vers 0,03. Sur 87 futures liquides du livre, la stationnarité arrivait avec d < 0,6. Jus d'orange et bovins vivants demandaient un d proche de 0. Une série explosive a d* > 1. Ces chiffres se remesurent. Le point t n'utilise que des prix connus à t. d et τ se calent sur la fenêtre d'entraînement.

## Fondamentaux

Une série fondamentale se joint à la date de publication, pas à la date de période. Le détail est dans ml4t-point-in-time.

## On s'arrête

- Entrer des prix bruts dans un modèle supervisé.
- Choisir d sur l'échantillon entier, puis prédire la fin.
- Une barre de temps par défaut quand le montant échangé est disponible.
- Recopier le d = 0,35 de l'E-mini.
- Une EWMA de seuil qui voit la barre en cours de construction.
- Poser un événement sur un croisement de Bollinger.

## Références

- López de Prado, The 10 Reasons Most Machine Learning Funds Fail, Journal of Portfolio Management, 44(6), 2018.
- Easley, López de Prado, O'Hara, The Volume Clock, Journal of Portfolio Management, 37(2), 2011.
- Clark, A Subordinated Stochastic Process Model with Finite Variance for Speculative Prices, Econometrica, 41(1), 1973.
- López de Prado, Advances in Financial Machine Learning, Wiley, 2018, chapitres 2 et 5.

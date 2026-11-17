---
name: mlp-causalite
description: >-
  Graphe causal avant un facteur. Use when a characteristic is about to enter a factor model or an optimizer.
---

# Facteurs et causalité

Invariants : finance-quantitative. Faux positifs de sélection : mlp-surapprentissage. Covariance et grappes : mlp-allocation. Régime pour la taille, définition écrite avant : ml4t-regime-awareness.

## Association et graphe

Une régression de caractéristique donne une association. Un modèle de facteur qui dit « toutes choses égales par ailleurs » dit une cause. López de Prado, Where are the Factors in Factor Investing, Journal of Portfolio Management, 49(5), 2023. Le graphe s'écrit avec le résultat : qui cause le rendement, quel confondeur, quelle collision. Sans ce graphe, le coefficient reste une association, et il n'entre pas dans un optimiseur comme un budget de risque.

López de Prado, Causal Factor Investing, Cambridge University Press, 2023, distingue deux affirmations fallacieuses.

Le type A est un faux positif de sélection. Le DSR et la PBO portent là-dessus. Le type B est une association qui peut être réelle, avec une spécification fausse (confondeur, collision). Contrôler les p-values ne corrige pas le type B. La prime peut bouger quand le confondeur bouge. Le livre relie ce second type au fait que des primes changent de régime dans la littérature.

## Ce que ça change pour l'allocation

López de Prado, Lipton et Zoonekynd, SSRN 5131050, 2025 : un modèle de facteur mal spécifié peut inverser les achats et les ventes, même si la moyenne et la covariance sont connues. Débruiter la matrice ne remplace pas le graphe.

Avant d'ajouter une caractéristique, on nomme une observation qui tuerait le mécanisme, et on la cherche. Une histoire de régime ajoutée après la mort de la prime est un ajout après coup. Elle ne compte pas comme le mécanisme écrit avant.

López de Prado, Ranking Empirical Evidence in Finance, SSRN 4425855, 2023, classe les preuves selon la facilité avec laquelle elles restent fausses. Une association en échantillon est en bas. Un mécanisme écrit avant le test, avec un résultat qui pourrait le réfuter, pèse plus. Les barreaux intermédiaires sont dans ce texte. On ne les invente pas.

## On s'arrête

- Faire entrer une caractéristique dans l'optimiseur parce que son t a passé 2.
- Appeler effet causal un coefficient dont le graphe n'est pas écrit.
- Traiter un modèle propre au sens des p-values comme propre au sens du type B.
- Ajouter un régime après avoir vu que la prime a disparu.

## Références

- López de Prado, Causal Factor Investing, Cambridge University Press, 2023.
- López de Prado, Where are the Factors in Factor Investing, Journal of Portfolio Management, 49(5), 2023.
- López de Prado, Ranking Empirical Evidence in Finance, SSRN 4425855, 2023.
- López de Prado, Lipton et Zoonekynd, Causal Factor Analysis is a Necessary Condition for Investment Efficiency, SSRN 5131050, 2025.

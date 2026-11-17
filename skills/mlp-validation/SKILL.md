---
name: mlp-validation
description: >-
  Purge, embargo, CPCV, importance des variables. Use when splitting a financial series or judging which features carry the score.
---

# Validation sans fuite

Invariants : finance-quantitative. Étiquettes : mlp-etiquetage. Fuite générale : ml4t-lookahead-bias. Surapprentissage du Sharpe : mlp-surapprentissage.

López de Prado, Journal of Portfolio Management, 44(6), 2018, pièges 2, 8 et 9.

## Purge et embargo

Un k-fold mélangé, et un découpage qui ne fait que respecter l'ordre, laissent fuir dès que l'étiquette regarde devant. La fuite demande que le couple (variables, étiquette) se ressemble des deux côtés du découpage. Des variables proches, ou des étiquettes proches, ne suffisent pas chacune seule.

L'étiquette i dépend de l'intervalle [t_i0, t_i1]. On retire de l'entraînement toute étiquette dont l'intervalle coupe celui d'une étiquette de test. Trois cas suffisent : le début du test tombe dans l'intervalle d'entraînement, la fin de l'entraînement tombe dans l'intervalle de test, l'entraînement englobe le test. Si le test est d'un seul tenant, un seul intervalle de test suffit. C'est la purge.

L'embargo retire un bloc d'entraînement juste après le test, à cause de la corrélation sérielle des variables. L'entraînement qui finit avant le début du test était déjà connaissable : on le garde. On allonge la fin de l'intervalle de test de h barres avant de purger. h est petit. L'article indique qu'un centième du nombre de barres suffit souvent. La valeur est écrite avant de voir le score. On vérifie que la performance cesse de monter quand le nombre de plis grandit. Si le score continue de monter quand le nombre de plis approche le nombre d'observations, le backtest vit de fuites.

Le groupe de test doit être long devant l'horizon des étiquettes. Sinon la purge vide l'entraînement. PurgedKFold suppose un test d'un seul tenant et shuffle à faux.

Le walk-forward a l'entraînement toujours avant le test. L'embargo n'y ajoute rien. La purge y reste : une étiquette peut commencer dans l'entraînement et finir dans le test. Le walk-forward se réconcilie avec un compte papier. Il ne teste qu'un chemin, et les premières décisions y voient peu de données. Un k-fold qui sert de scénario de stress, lui, entraîne aussi sur le futur du bloc testé. Il a besoin de la purge et de l'embargo. Son chiffre n'est pas une performance historique. Il produit une prévision par observation.

Les fonctions de score de sklearn, dans l'état décrit par le livre (2018), ignoraient l'index des classes (issue 6231) et ne passaient pas sample_weight à la perte log dans cross_val_score (issue 9144). Sur sklearn 1.9.1, contrôlé le 2026-10-29, `params` envoie le poids à l'ajustement. Un scoreur maison du même appel a reçu `sample_weight` à None. On note encore le pli soi-même, en neg_log_loss ou en accuracy. `Pipeline.fit` refuse `sample_weight` nu : on le passe en `etape__sample_weight`. Le choix du score est dans mlp-modeles.

## CPCV

Le walk-forward se surajuste aussi bien à l'endroit qu'à l'envers. Jouer la série à l'envers ne donne pas, en systématique, un meilleur résultat que l'endroit. L'argument qui voudrait que prédire le passé soit trop facile ne tient donc pas.

La validation croisée combinatoire purgée (CPCV) découpe la série en N groupes ordonnés, sans mélange. Les N - 1 premiers ont pour taille la partie entière de T/N. Le dernier prend le reste. Chaque test prend k groupes. L'entraînement voit la fraction 1 - k/N. Le nombre de découpes est C(N, k). Le nombre de chemins de backtest est C(N - 1, k - 1). Pour 6 groupes et k = 2 : 15 découpes, 5 chemins. Chaque groupe est testé autant de fois que les autres. Purge et embargo s'appliquent à chaque découpe.

On publie la distribution des Sharpe de ces chemins. Un chemin est un tirage. Les chemins réutilisent les mêmes observations, ils ne sont pas des échantillons indépendants. Plus de chemins n'ajoute pas de données.

## Importance des variables

L'outil de recherche est l'importance, pas une boucle de backtests. On ajuste avec la purge, puis on demande de quelles variables le score dépend.

L'importance par permutation (MDA) se mesure sur le pli de test : on permute une variable, on regarde la baisse du score. Le pli est purgé et embargo. Une baisse négative veut dire que la variable nuit. La MDA peut conclure que toutes les variables sont inutiles. Pour le méta-étiquetage, le score est le F1. Si le score n'est pas une métrique, la MDA est un rang. On rapporte la baisse relativement au meilleur score possible : 0 pour la perte log, 1 pour l'accuracy. L'importance par impureté (MDI) est dans l'échantillon. Elle partage l'importance entre des variables qui se remplacent, et elle favorise celles qui offrent plus de coupures. Ce n'est pas le chiffre publié. L'importance d'une variable seule (SFI) dit ce qu'elle porte sans les autres. Elle rate les effets joints.

Avant une MDI ou une MDA, on orthogonalise. On standardise, on diagonalise, on garde les composantes jusqu'à une part de variance écrite avant. L'exemple du livre s'arrête à 95 %. L'ACP ne voit pas l'étiquette. Un accord entre le rang de l'ACP et le rang d'importance, tau de Kendall pondéré calculé sur l'inverse du rang de l'ACP (le poids porte sur les premières variables), va contre un pur hasard. Le tau de la figure du livre, proche de 0,82, est celui de cette figure.

Si deux variables se remplacent, on les permute ensemble. Sinon chacune paraît faible (López de Prado, Machine Learning for Asset Managers, Cambridge, 2020). Le regroupement se fait sur la fenêtre d'entraînement. Une importance qui ne tient que dans un régime se rapporte par régime. La définition du régime est écrite avant : ml4t-regime-awareness.

Deux dessins. En parallèle : un modèle par titre, puis on agrège. Une variable haute sur beaucoup de titres, et haute pour la MDI, la MDA et la SFI, mérite une étude de mécanisme. La substitution peut échanger les rangs d'un titre à l'autre. Moyenner sur un univers large réduit cet écart. Empilé : on empile les titres après une standardisation glissante sur le passé, pour rapprocher les lois, et un seul modèle apprend l'importance. L'échantillon est plus grand, le score n'est pas dilué par la moyenne, et on surajuste moins un titre. Ça coûte de la mémoire (mlp-modeles). L'auteur du livre retient l'empilement pour l'importance et pour la prévision. Une variable qui ne compte que sur un titre est une candidate à la fausse découverte.

## On s'arrête

- `KFold(shuffle=True)` sur une série de prix.
- Un `TimeSeriesSplit` sans purge quand l'étiquette a un horizon.
- Choisir les variables en relançant le backtest.
- Publier une MDI comme preuve hors échantillon.
- Lire un seul Sharpe de walk-forward comme une distribution.
- Appeler `cross_val_score` sans avoir vérifié que le pli reçoit les poids et les étiquettes.

## Références

- López de Prado, The 10 Reasons Most Machine Learning Funds Fail, Journal of Portfolio Management, 44(6), 2018.
- López de Prado, Advances in Financial Machine Learning, Wiley, 2018, chapitres 7, 8 et 12.
- López de Prado, Machine Learning for Asset Managers, Cambridge University Press, 2020.

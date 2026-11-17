---
name: mlp-modeles
description: >-
  Ensembles, recherche purgée, perte log. Use when fitting a classifier or tuning its hyperparameters.
---

# Ajustement

Invariants : finance-quantitative. Découpage et score du pli : mlp-validation. Étiquettes, unicité, F1 : mlp-etiquetage. Chaque essai compte : mlp-surapprentissage. Le poste de cette machine : poste-dev.

López de Prado, Advances in Financial Machine Learning, Wiley, 2018, chapitres 6, 9 et 20. Les chapitres 21 et 22, grappes de machines et cartes graphiques, restent hors de ce skill.

## Bagging

N classifieurs de précision individuelle p supérieure à 1/k battent la moyenne quand N est grand (jury de Condorcet). Le bagging ne rattrape pas une précision très inférieure à 1/k.

Des étiquettes redondantes rendent les échantillons du sac presque identiques. La corrélation moyenne approche 1, le bagging ne réduit plus la variance, et la précision hors sac est gonflée : le hors sac ressemble au sac. En finance, on ne publie pas la précision hors sac. L'évaluation est un k-fold purgé, stratifié, sans mélange, avec un k petit.

Une forêt ajoute un tirage d'attributs. Si les observations sont redondantes, la forêt de sklearn tire encore un échantillon de la taille de l'apprentissage, et les arbres se ressemblent. On baisse max_features. On arrête tôt avec min_weight_fraction_leaf, jusqu'à ce que le hors sac rejoigne le score du k-fold. On peut aussi emballer un arbre, ou une forêt à un arbre, avec max_samples égal à l'unicité moyenne et max_features = 1. Le bootstrap séquentiel remplace le bootstrap usuel (mlp-etiquetage). Le poids de classe du bagging est balanced_subsample. Ajuster la forêt sur une ACP des variables raccourcit les arbres.

Le boosting réduit le biais et la variance. Sur un faible rapport signal sur bruit, il surajuste, et il est séquentiel. On retient le bagging : il limite le surapprentissage et se parallélise. Si le bagging dégrade la stratégie, elle tenait sur peu d'observations ou sur des points extrêmes.

Un apprenant qui ne passe pas à l'échelle, un SVM par exemple, s'emballe en beaucoup de copies arrêtées tôt : max_iter bas, ou tolérance plus haute.

## Recherche

La grille et le tirage aléatoire reçoivent le générateur purgé. Sans lui, la recherche surajuste sur de l'information qui a fui. La grille essaie toutes les combinaisons. Elle devient hors de prix quand les paramètres sont nombreux. Le tirage fixe le nombre d'essais. Un paramètre peu utile n'allonge plus le temps, comme il le ferait dans une grille.

Un paramètre positif dont l'effet suit à peu près le logarithme, C d'un SVC ou gamma d'un noyau RBF, se tire en log-uniforme. log(x) est uniforme entre log(a) et log(b), avec a > 0 et b > a. La fonction de répartition ne dépend pas de la base du logarithme. Un uniforme sur [0, 100] place presque tous les tirages au-dessus de 1. Pour un SVC, passer C de 0,01 à 1 compte autant que de 1 à 100.

Score. Méta-étiquetage : F1. Ailleurs, pour une stratégie : neg_log_loss. L'accuracy traite une erreur très sûre comme une erreur peu sûre, et elle peut compenser un raté sûr par un succès peu sûr. La stratégie gagne sur le bon signe tenu avec une probabilité haute. La perte log est la log-vraisemblance de ces probabilités. Changer les noms des classes ne change ni l'accuracy ni neg_log_loss. Ça change le F1.

Pipeline.fit ne prend pas sample_weight en argument direct. On le passe par fit_params, tant que la version installée ne fait pas mieux. On note le pli soi-même (mlp-validation). Chaque combinaison lancée entre dans le nombre d'essais.

## Calcul

On vectorise d'abord : une opération sur tout le tableau, pas une boucle imbriquée dont la profondeur dépend d'un paramètre. En Python, le verrou global limite l'écriture à un fil par cœur. Le parallélisme passe par des processus, qui ne partagent pas la mémoire.

Une tâche indivisible est un atome. On groupe les atomes en molécules. Chaque molécule est traitée en séquence, dans un processus. Le parallélisme est entre molécules. Le découpage linéaire prend un nombre de molécules égal au minimum entre le nombre de processus et le nombre d'atomes, en parts égales. Deux boucles imbriquées, un SADF ou des barrières, ne se coupent pas ainsi : les molécules lourdes n'ont pas le même coût. On les met en tête de file, ou on équilibre le nombre d'opérations par molécule. Des processus qui exécutent du code vectorisé, sur plusieurs nœuds, font trois niveaux. Le nombre de cœurs de cette machine se lit dans poste-dev, pas dans l'exemple à 24 processus du livre.

## On s'arrête

- Publier la précision hors sac d'une forêt dont les étiquettes se recouvrent.
- Une recherche d'hyperparamètres avec un KFold mélangé.
- Tirer C ou gamma uniformément sur un grand intervalle.
- Passer au boosting parce que le score d'entraînement est meilleur.
- Compter sur des threads Python pour utiliser les cœurs.
- Une double boucle SADF laissée en séquentiel par défaut.

## Références

- López de Prado, Advances in Financial Machine Learning, Wiley, 2018, chapitres 6, 9 et 20.

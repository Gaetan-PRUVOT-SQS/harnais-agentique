---
name: mlp-etiquetage
description: >-
  Triple barrière, méta-étiquetage, poids d'unicité. Use when labeling a trade, sizing a bet, or weighting overlapping outcomes.
---

# Étiquettes et poids

Invariants : finance-quantitative. Série : mlp-series. Fuite : ml4t-lookahead-bias. Validation : mlp-validation. Ajustement : mlp-modeles.

López de Prado, Journal of Portfolio Management, 44(6), 2018, pièges 5, 6 et 7. Le détail vient de Advances in Financial Machine Learning, Wiley, 2018, chapitres 3, 4, 10 et 13.

## Triple barrière

L'horizon fixe applique le même seuil à une nuit calme et à une ouverture. L'étiquette ne correspond pas à une sortie de position. La volatilité du jour est l'écart-type, en moyenne mobile exponentielle, des rendements connus à l'entrée.

Deux barrières horizontales, en unités de cette volatilité (réalisée ou implicite, fenêtre passée). Une barrière verticale, en nombre de barres : la première barre à partir de l'événement plus le nombre de jours retenus. L'étiquette est le premier contact. Haut : 1. Bas : -1. Verticale : le signe du rendement à l'échéance, ou 0. Le choix est écrit avant le premier ajustement. Le signe garde un gain ou une perte réalisé. Le 0 sort l'observation de la classe directionnelle.

Les barrières horizontales peuvent être asymétriques. Apprendre le sens demande des barrières symétriques, ou pas de barrière horizontale. Le chemin compte : le rendement de l'étiquette va de l'entrée au premier contact.

On ne raccourcit pas l'horizon pour faire disparaître les chevauchements. La fin de l'étiquette i peut dépasser le début de l'étiquette i + 1. L'unicité qui utilise cette fin future est un poids d'entraînement. Elle n'entre pas dans les variables.

## Largeurs

Les largeurs de prise de profit et de stop ne se choisissent pas en maximisant le Sharpe sur le chemin historique. Deux paramètres libres sur I occasions surajustent, surtout quand le résultat est autocorrélé. Une paire qui vise quelques points extrêmes est le cas trivial.

On caractérise le processus des prix. Le livre prend un Ornstein-Uhlenbeck discret, stationnaire pour φ dans (-1, 1). On estime σ et φ par régression sur la forme linéarisée, sur tout l'échantillon qui sert à décrire le processus. On construit une grille de paires. On simule un grand nombre de chemins (l'exemple du livre en prend 100 000) depuis les conditions initiales observées, avec une durée maximale égale à la barrière verticale (l'exemple prend 100 observations). Chaque paire reçoit le Sharpe de ces chemins. On retient la paire, ou le stop compatible avec une prise de profit déjà imposée, ou la prise de profit compatible avec un stop déjà imposé.

La conjecture du livre : pour ce processus, une paire unique maximise le Sharpe. Elle n'est pas prouvée. Les cartes du chapitre 13 sont des illustrations. Quand le processus se rapproche d'une marche aléatoire, bouger la paire change peu le Sharpe. La relation entre φ et la demi-vie n'est pas recopiée ici : la lire au chapitre 13. Cette recherche règle une sortie d'investissement. Un trader d'exécution qui hérite d'une position déjà ouverte a une autre question.

## Méta-étiquetage

Le sens (acheter ou vendre) et la taille sont deux décisions. Le sens vient d'un modèle primaire, qui peut être un modèle fondamental, une équation, ou un appel discrétionnaire. La taille vient d'un second modèle, qui apprend si le pari du premier a gagné. Le second ne cherche pas un nouveau sens.

Le rendement de l'étiquette est multiplié par le sens du primaire. Le bin est le signe de ce rendement, puis 0 quand le rendement est négatif ou nul. Les étiquettes du second sont dans {0, 1}. On écarte les étiquettes trop rares.

On vise un primaire à fort rappel. Le second filtre les faux positifs. Le score suivi est le F1, moyenne harmonique de la précision et du rappel : 2 P R / (P + R), avec P = vrais positifs / (vrais positifs + faux positifs) et R = vrais positifs / (vrais positifs + faux négatifs). Un second qui prédit tout à 0 a un rappel nul, une précision non définie, et une accuracy haute. sklearn met alors le F1 à 0 et avertit. Si les cas positifs dominent, on inverse la classe positive avant le F1. Sinon un modèle qui prédit tout à 1 a un F1 au moins aussi haut que l'accuracy, sans rien discriminer.

## Poids

Deux étiquettes sont concurrentes à t si elles dépendent du même rendement de barre. c_t est leur nombre. L'unicité de l'étiquette i à t vaut 1/c_t sur son intervalle, 0 ailleurs. L'unicité moyenne est la moyenne de ces termes sur la vie de l'étiquette, donc l'inverse de la moyenne harmonique des c_t.

Le bootstrap usuel de I éléments en garde environ 1 - e^{-1}, soit deux tiers, distincts. S'il n'existe que K issues sans recouvrement, chaque issue est tirée en moyenne I/K fois, et I/K vaut au moins 1. Le bootstrap usuel suréchantillonne. On ne jette pas les recouvrements partiels.

On pose max_samples à la moyenne des unicités moyennes, sur l'estimateur qui a ce paramètre. sklearn 1.9.1 l'a sur BaggingClassifier et sur RandomForest, contrôle du 2026-10-29. Une version qui ne l'a pas : on emballe un arbre. Mieux : le bootstrap séquentiel. Le premier tirage est uniforme. Après un ensemble de tirages, l'unicité d'un candidat est son indicateur divisé par un plus la somme des indicateurs déjà tirés, à chaque barre, puis moyenne sur sa vie. Sa probabilité est cette unicité divisée par la somme des unicités. La matrice d'indicateurs a une colonne par observation et une ligne par barre, avec un 1 sur la vie de l'étiquette. L'exemple du livre (10 observations, 100 barres, horizon max 5) trouve une médiane d'unicité moyenne de 0,6 en bootstrap usuel et de 0,7 en séquentiel. Ce sont des exemples.

Le poids brut est la valeur absolue de la somme, sur l'intervalle, du rendement de barre divisé par c_t. L'article pose ce rendement en p_t / p_{t-1} - 1. On renormalise pour que la somme des poids égale le nombre d'étiquettes. sklearn suppose un poids de 1. Ces poids entrent dans l'ajustement.

On retire l'étiquette neutre. Un petit rendement prendrait sinon un gros poids, et un ±1 peu sûr dit déjà de passer.

La décroissance est linéaire par morceaux sur l'unicité cumulée, pas sur le calendrier. Sur le calendrier, les observations redondantes décroissent trop vite. L'observation la plus récente a le poids 1. Le paramètre du livre, noté c, est dans (-1, 1]. c = 1 : pas de décroissance. Entre 0 et 1 : linéaire et strictement positif. c = 0 : le plus ancien atteint 0. c négatif : on efface la fraction |c| la plus ancienne de l'unicité cumulée.

Poids de classe : balanced sur les étiquettes {-1, 1}. Pour un bagging, balanced_subsample. Des poids qui ne somment pas au nombre de classes changent la régularisation. L'anomalie sklearn sur class_weight (issue 4324, signalée dans le livre) se vérifie sur la version installée.

## Taille

Une prévision juste peut perdre de l'argent si la taille est fausse. Trois méthodes, indépendantes de la stratégie.

La concurrence des paris : nombre de longs ouverts moins nombre de courts ouverts. On ajuste un mélange de deux gaussiennes. Pour une concurrence c positive ou nulle, la taille vaut (F[c] - F[0]) / (1 - F[0]). Pour c négatif, (F[c] - F[0]) / F[0]. F est la fonction de répartition du mélange.

Le budget : longs ouverts sur le maximum de longs, moins courts ouverts sur le maximum de courts. Le dernier signal concurrent peut encore entrer.

La probabilité du second modèle. Deux classes : z = (p - 1/2) / √(p (1 - p)), taille m = 2 Φ(z) - 1. Plus de deux classes, un contre le reste : p~ est la plus grande probabilité, z = (p~ - 1/|X|) / √(p~ (1 - p~)), et la taille est le signe de la classe fois (2 Φ(z) - 1). On moyenne les tailles des paris encore ouverts jusqu'à leur fin. On ne remplace pas l'ancienne taille par la nouvelle. On discrétise : m* = arrondi(m / d) fois d, avec d dans (0, 1]. L'exemple du livre prend d = 0,2. On borne ensuite à [-1, 1].

Taille qui suit un prix prévu f et un prix de marché p. x = f - p. m = x / √(ω + x²). La position cible est la partie entière de m fois la position maximale. Le prix limite moyen, pour les parts que l'on ajoute, vaut f - m √(ω / (1 - m²)), afin que l'ordre ne réalise pas une perte quand p rejoint f. On cale ω = x² (m*^{-2} - 1) sur une paire (écart, taille) choisie avant. L'alternative en puissance est le signe de x fois |x| à la puissance ω. L'exemple chiffré du livre (écart 10, taille 0,95, position max 100) n'est pas un défaut.

## On s'arrête

- Un seuil d'étiquette constant quand la volatilité change d'un ordre de grandeur.
- Un seul modèle qui apprend le sens et la taille.
- Des poids égaux sur des étiquettes qui partagent les mêmes barres.
- Une volatilité de barrière calculée avec des prix postérieurs à l'entrée.
- Raccourcir l'horizon pour supprimer les chevauchements, puis utiliser la fin de l'étiquette comme variable.
- Caler le stop et la prise de profit sur le Sharpe du chemin historique.
- Empiler les tailles des paris encore ouverts au lieu de les moyenner.

## Références

- López de Prado, The 10 Reasons Most Machine Learning Funds Fail, Journal of Portfolio Management, 44(6), 2018.
- López de Prado, Advances in Financial Machine Learning, Wiley, 2018, chapitres 3, 4, 10 et 13.

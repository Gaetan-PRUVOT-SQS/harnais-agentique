---
name: mlp-traits
description: >-
  Ruptures, entropie, variables de flux. Use when a price series becomes a feature before a model.
---

# Traits d'une série de prix

Invariants : finance-quantitative. Horloge et filtre d'événements : mlp-series. Exécution, impact et file : microstructure-marche. Régime pour la taille : ml4t-regime-awareness. Fuite : ml4t-lookahead-bias.

Ces traits sont des variables. Ils ne donnent pas un signal de sortie. López de Prado, Advances in Financial Machine Learning, Wiley, 2018, chapitres 17, 18 et 19.

## Ruptures

Deux familles. Elles ne sont pas le filtre à somme cumulée qui pose un événement (mlp-series). Ici la somme porte sur des erreurs de prévision, ou sur l'explosivité. Une bulle comprend les ventes en cascade.

Résidus récursifs (Brown, Durbin et Evans). Le résidu est l'erreur à un pas d'une régression dont les coefficients ne voient que le passé. S_t cumule ce résidu standardisé. Sous des coefficients constants, S_t suit une normale de variance t - k - 1. La date de départ est un choix, et elle change le test.

Chu, Stinchcombe et White, sur les niveaux, sans dérive. S_{n,t} = (y_t - y_n) / (σ estimé √(t - n)). Le seuil unilatéral vaut √(b_α + log(t - n)). Le livre cite b à 5 % égal à 4,6, issu de leur Monte Carlo. On ne l'ancre pas sur une seule date : on prend le sup des fenêtres arrière.

Un Dickey-Fuller de type Chow suppose une seule rupture, qui dure jusqu'à la fin de l'échantillon. Le SADF (Phillips, Wu et Yu, International Economic Review, 2011) relâche cette hypothèse. À chaque date de fin t, on prend le sup des t de ADF sur les départs arrière, avec une longueur minimale τ. Le sup est sensible aux points extrêmes. Un ADF de quantile (l'exemple du livre prend q = 0,95) et un ADF conditionnel bougent moins. Le SADF est le cas q = 1.

On le calcule sur les log-prix. L'ADF sur le prix brut suppose une variance de rendement indépendante du niveau. Ça casse sur des décennies de hausses. Trois états de la régression en log, sans retard. β < 0 : régime stable, demi-vie -log(2) / log(1 + β). β = 0 : martingale. β > 0 : explosif, selon que le log de départ est au-dessus ou au-dessous de l'équilibre instable.

Le SADF naïf fait de l'ordre de T² ajustements. On ne le laisse pas en double boucle par défaut. La boucle interne prend des log-prix, une longueur minimale, une constante (aucune, tendance linéaire, ou quadratique) et un nombre de retards. Le découpage du calcul est dans mlp-modeles.

## Entropie

L'entropie mesure l'information portée par les prix. Un momentum sert quand ils en portent peu. Un retour à la moyenne sert quand ils en portent beaucoup.

H est l'entropie de Shannon. La redondance vaut 1 - H / log2 de la taille de l'alphabet. L'information mutuelle de deux gaussiennes vaut -(1/2) log(1 - ρ²).

L'estimateur par fréquences compte les mots de longueur w. Il lui faut un n très supérieur à w.

Lempel-Ziv, dans la version de Kontoyiannis : le taux d'entropie est l'inverse de la longueur moyenne du plus long appariement, mesurée en bits. La fenêtre d'appariement est centrée, les deux chaînes ont la même longueur. Sinon le maximum est sous-estimé. On retient l'estimateur qui met log2 de la fenêtre au numérateur, pour éviter la condition de Doeblin.

Fenêtre glissante : on prend k proche de (log2 n)², donc une longueur totale proche de n plus ce carré. L'exemple du livre, longueur 2⁸, donne n proche de 198 et k proche de 58. Fenêtre qui s'allonge : le message a une longueur paire. S'il est court, on le répète. Si la fin compte, on le retourne. On encode une série différenciée en fractionnaire (mlp-series), pas des rendements d'ordre 1.

L'encodage binaire (le signe, zéros écartés) jette l'ampleur, sauf si l'échantillonnage fixe déjà cette ampleur (barrières symétriques) ou si une horloge en volume ou en notionnel calme l'hétéroscédasticité. Les quantiles fixent l'alphabet sur l'entraînement et gonflent l'entropie. Découper la plage observée en tranches de largeur égale produit des lettres rares. L'entropie d'une gaussienne, (1/2) log(2 π e σ²), vaut environ 1,42 pour une normale centrée réduite. Un alphabet sous une dizaine de lettres la sous-estime. C'est la figure du livre, sur des séries de longueur 100. La volatilité déduite de l'entropie, exp(H) / √(2 π), ne vaut que si les rendements sont normaux.

## Flux

Ces variables décrivent le flux passé. Le prix exécutable et le lambda de Kyle comme modèle d'impact sont dans microstructure-marche. On ne les y redéfinit pas. Sans barre précédente, le premier signe de ce chapitre vaut 1. Le constructeur de barres, lui, reprend le signe précédent (mlp-series).

Roll : le demi-spread effectif est la racine de max(0, moins la covariance sérielle des variations de prix). On s'en sert quand les cotations manquent ou ne représentent pas le marché, par exemple des obligations d'entreprise, municipales ou d'agence.

La variance de Parkinson utilise le plus haut et le plus bas. Corwin et Schultz estiment le spread sur le plus haut et le plus bas de deux barres. Un alpha négatif est mis à 0. Le t de Student de l'estimation informe souvent plus que la moyenne.

Comme variable, le lambda de Kyle est la pente de la variation de prix sur le volume signé. Amihud est le rendement absolu de la barre divisé par le volume en devise de la barre. La liquidité qui change la taille est dans ml4t-regime-awareness. Hasbrouck régresse le log-rendement sur la racine signée du volume en devise, de préférence sur des barres d'activité. L'horloge de cinq minutes de l'article d'origine est un pis-aller.

Le PIN : quand la probabilité que l'informé soit acheteur vaut un demi, le spread attendu suit α μ / (α μ + 2 ε).

Le VPIN se calcule sur des barres de volume : moyenne de la valeur absolue du volume acheteur moins le volume vendeur, divisée par le volume de la barre. Une régression linéaire peut rater son contenu. Le livre le note, entre Andersen et Bondarenko et les études qui ont suivi. On ne tranche pas sur une seule régression.

Sans modèle fermé : la fréquence des tailles rondes (traders au clic), le taux d'annulation, le taux d'ordres au marché. Eisler et al. (2012), cités au chapitre 19, trouvent que les petites capitalisations ne répondent pas comme les grandes.

## On s'arrête

- Confondre le filtre qui pose un événement et le test qui cherche une rupture.
- Un SADF sur des prix bruts couvrant des décennies.
- Encoder des rendements d'ordre 1 pour y lire une mémoire.
- Prendre la volatilité d'entropie sans avoir vérifié la normalité.
- Régler une exécution avec le VPIN de cette page.
- Une variable de flux qui voit des trades postérieurs à la décision.

## Références

- López de Prado, Advances in Financial Machine Learning, Wiley, 2018, chapitres 17, 18 et 19.
- Phillips, Wu et Yu, International Economic Review, 2011. Le SADF du chapitre 17 renvoie à cet article.

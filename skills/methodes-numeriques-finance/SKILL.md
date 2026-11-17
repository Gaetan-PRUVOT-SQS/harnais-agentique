---
name: methodes-numeriques-finance
description: >-
  Monte-Carlo, EDP et calibration avec un oracle fermé. Use when simulating, solving a pricing PDE, or testing a pricer.
---

# Méthodes numériques

Invariants : finance-quantitative. Le produit et la nappe : pricing-derives. La courbe : revenu-fixe.

Produit, marché, modèle et moteur restent séparés. Changer une courbe ne réécrit pas le payoff. Si le dépôt a déjà QuantLib, on suit son découpage Instrument, TermStructure, PricingEngine. On n'ajoute pas la librairie pour l'occasion.

Le test fige la graine et la tolérance, absolue et relative.

## Oracle

Le cas simple a une formule fermée, ou une deuxième méthode (transformée, arbre, EDP) sur les mêmes entrées. Les identités ci-dessous passent avant un exotique.

Parité call-put européenne, dividende continu `q`, taux continu `r` :

`C - P = S exp(-q T) - K exp(-r T)`

Martingale du sous-jacent sous la mesure cash :

`exp(-r T) E[S_T] = S exp(-q T)`

Vol nulle, ou maturité nulle : le call vaut `max(S exp(-q T) - K exp(-r T), 0)`.

L'américain vaut au moins l'européen. Le call baisse avec le strike, et il est convexe en le strike (pricing-derives).

```python
import math


def parite_call_put(call, put, spot, strike, taux, dividende, maturite):
    membre = spot * math.exp(-dividende * maturite) - strike * math.exp(-taux * maturite)
    return math.isclose(call - put, membre, rel_tol=1e-12, abs_tol=1e-12)
```

## Monte-Carlo

Un prix est une moyenne, un intervalle (erreur statistique), et un biais de discrétisation. Le biais se voit en raffinant le pas, ou en comparant à la formule exacte.

Euler-Maruyama : ordre faible 1, ordre fort 1/2, quand les coefficients sont lipschitziens (Kloeden et Platen). Un pas grossier ne fait pas un prix.

Réduction de variance : variables antithétiques ; variable de contrôle dont l'espérance est connue en fermé ; échantillonnage préférentiel, avec la mesure écrite. Une variance plus petite ne corrige pas un biais.

Grecques : pathwise ou adjoint sur un payoff lisse. Un digital ou une barrière observée en discret se lisse, ou se mélange au likelihood ratio, puis se vérifie au bump. Le pas du bump est un paramètre du test. Trop fin, il se noie dans le bruit. Trop large, il n'est plus une dérivée.

Quasi Monte-Carlo (Sobol) pour une dimension modérée. On le randomise si on veut un intervalle. Un long chemin a une dimension effective qui casse un Sobol naïf : bridge brownien ou ACP avant.

## EDP

Le domaine, les conditions aux bords et le schéma sont écrits. Implicite ou Crank-Nicholson pour le cas courant. Un schéma explicite a une condition de stabilité. Un prix qui oscille quand on raffine ne sort pas.

L'exercice anticipé est une contrainte du schéma : à chaque pas, la valeur reste au-dessus du payoff.

Deux grilles (pas de temps, pas d'espace) qui diffèrent de plus que la tolérance ne font pas un prix.

## Calibration

Moins de paramètres libres que de prix informatifs. Le résidu se publie par instrument, pas seulement en somme. Les poids sont un choix écrit (vega, ou liquidité).

Les contraintes de non-arbitrage sont dans le problème. Un filtre après coup arrive trop tard.

La même procédure se relance sur un second jour. Une calibration qui ne tient qu'aujourd'hui n'est pas stable.

Un optimiseur non borné sur une surface non convexe ne donne pas un optimum unique. On publie les bornes et le point de départ.

## Adjoint

L'adjoint est le mode de production quand le livre a beaucoup de grecques. Il se vérifie contre un bump sur un sous-ensemble de risques, dont un risque qui traverse une discontinuité.

## Arbres

Un arbre sert d'oracle en une dimension, avec le pas écrit. Un arbre CRR sur une barrière continue est biaisé. Le lissage de la barrière fait partie du test.

## On s'arrête

- Un prix Monte-Carlo sans intervalle et sans regard sur le pas de temps.
- Une grecque pathwise sur un digital, sans bump de contrôle.
- Une calibration jugée sur la seule somme des résidus.
- `==` entre deux prix flottants.

## Références

- Kloeden et Platen, Numerical Solution of Stochastic Differential Equations, Springer, 1992.
- Glasserman, Monte Carlo Methods in Financial Engineering, Springer, 2003. Réduction de variance, pathwise, likelihood ratio.

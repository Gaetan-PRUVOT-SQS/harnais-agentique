---
name: pricing-derives
description: >-
  Prix, grecques et nappe de vol sans arbitrage. Use when pricing an option, marking a smile, or choosing local, stochastic or rough vol.
---

# Prix des dérivés

Invariants : finance-quantitative. Coder le pricer : methodes-numeriques-finance (parité, martingale, vol nulle).

## Mesure

Le numéraire est nommé. Le changement de mesure (Girsanov, changement de numéraire) est celui qui rend le prix actualisé une martingale sous ce numéraire. Un prix « risque-neutre » sans dire le numéraire (cash, annuity, asset) est incomplet.

Le forward du sous-jacent inclut les dividendes discrets déjà détachés de la période, ou le taux de dividende continu du contrat. Un call sur le spot nu, alors que le forward décote un dividende, est un autre produit.

## Nappe

Avant interpolation, la nappe passe trois tests.

Bornes d'un call européen, dividende continu `q`, taux continu `r` : le prix est entre `max(S exp(-qT) - K exp(-rT), 0)` et `S exp(-qT)`.

Papillon : le call est convexe en le strike. Pour `K` entre `K1` et `K3`, le prix en `K` reste sous la corde. Une densité négative se voit là.

Calendrier : la variance totale `σ(k, T)² T` ne baisse pas avec `T` à moneyness log fixe `k = log(K / F_T)` (Gatheral et Jacquier, Quantitative Finance, 2014). Une baisse est une cote à contester ou un arbitrage à retirer, pas un point par lequel on interpole.

On interpole en variance totale, ou avec une forme sans arbitrage (SVI tenu par ces contraintes), puis on refait le papillon sur une grille de strikes. Un lissage qui casse une contrainte se rejette.

## Quel modèle

Black-Scholes sert d'oracle et de quote (vol implicite). Couverture continue, vol constante, pas de saut. La nappe existe parce que ces hypothèses lâchent. Le delta de couverture d'un livre avec skew est celui du modèle qui porte le skew. Le résidu (saut, vol de vol) est un stress à côté du prix.

Vol locale (Dupire, Risk, 1994) : la surface du jour fixe la vol locale. Les vanilles européennes ressortent. La dynamique du smile futur est une fonction déterministe du spot. Un barrier ou un forward-starting en vol locale pure a cette limite écrite à côté du prix.

Vol stochastique à un facteur (Heston) : le skew action passe par une corrélation spot-variance négative. Si la condition de Feller `2 κ θ ≥ ξ²` ne tient pas, la variance peut toucher zéro. On l'écrit à côté du calage. Les ailes ne se règlent pas toutes seules.

SABR (Hagan, Kumar, Lesniewski, Woodward, Wilmott, 2002) : une tranche de smile, utile en taux (version normale si le taux peut être négatif ou nul). Le développement brut donne une densité négative dans l'aile basse. Un strike bas se vérifie contre une densité positive, ou contre l'intégration d'un SABR absorbé.

Vol locale-stochastique : quand le livre de vanilles et le livre d'exotiques doivent être marqués ensemble. La vol locale pure ne fait pas les deux.

Vol rough : le smile court colle mieux au marché, le calcul coûte. On la prend quand le court terme est le risque du livre.

## Grecques

Un payoff lisse : pathwise, ou l'adjoint si le livre a beaucoup de risques. Un digital, ou une barrière observée en discret, a un payoff discontinu : le pathwise est biaisé. On lisse, ou on mélange avec le likelihood ratio, puis on vérifie au bump.

Le bump est un oracle de l'adjoint. Le pas est écrit. Un pas qui traverse une barrière ou une maille de strike n'est plus une dérivée.

Vega, thêta et rhô bumpent la donnée de marché que le livre couvre, pas un paramètre caché dans la calibration.

## Exercice anticipé

L'américain vaut au moins l'européen. Un solveur qui rend moins a un bug.

Call américain sur une action sans dividende discret et sans taux de dividende : même prix que l'européen (Merton, Bell Journal of Economics, 1973). Le put américain s'exerce, lui. Un dividende discret peut rendre l'exercice du call rationnel.

## Options sur futures

Black 76 pour une option à prime payée d'avance. Une option margée comme un future (la prime n'est pas payée cash au départ) ne se décote pas de la même façon. Le contrat dit laquelle. Le test à vol nulle rend l'intrinsèque de la convention choisie.

## On s'arrête

- Interpoler une nappe qui a déjà un papillon négatif.
- Couvrir un livre de skew avec le seul delta Black-Scholes, sans stress de saut ou de vol.
- Livrer un exotique en vol locale sans écrire la dynamique du smile futur.
- Un américain sous l'européen.

## Références

- Gatheral et Jacquier, Arbitrage-free SVI volatility surfaces, Quantitative Finance, 2014.
- Dupire, Pricing with a smile, Risk, 1994.
- Hagan, Kumar, Lesniewski, Woodward, Managing Smile Risk, Wilmott, 2002.
- Merton, Theory of Rational Option Pricing, Bell Journal of Economics, 1973.

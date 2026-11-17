---
name: finance-quantitative
description: >-
  Porte d'entrée : unités, sans arbitrage, risque de modèle, carte MSFE. Use when pricing, hedging, curving, backtesting, or doing financial engineering.
---

# Finance quantitative

Charger ce skill, puis un seul skill de sujet. Les invariants d'ici valent partout. On ne les recopie pas ailleurs.

Code : pratiques-dev-senior. Un pricer est du code, avec tests et erreurs explicites.

## Quel skill

| Sujet | Skill |
|-------|-------|
| Prix, vol, grecques, exotique | pricing-derives |
| Courbe, swap, obligation, swaption | revenu-fixe |
| VaR, expected shortfall, XVA, crédit, limites | risque-quantitatif |
| Monte-Carlo, EDP, calibration, pricer | methodes-numeriques-finance |
| Allocation, coûts, Sharpe, capacité | portefeuille-quantitatif |
| Carnet, spread, impact, exécution | microstructure-marche |
| Fuite d'information future | ml4t-lookahead-bias |
| Fondamentaux, révisions, jointure datée | ml4t-point-in-time |
| Régime pour la taille de position | ml4t-regime-awareness |
| Barres, différenciation fractionnaire | mlp-series |
| Ruptures, entropie, variables de flux | mlp-traits |
| Triple barrière, méta-étiquetage, poids | mlp-etiquetage |
| Purge, embargo, CPCV, importance | mlp-validation |
| Ensembles, recherche purgée | mlp-modeles |
| Sharpe dégonflé, PBO, nombre d'essais | mlp-surapprentissage |
| HRP, débruitage, grappes | mlp-allocation |
| Graphe causal d'un facteur | mlp-causalite |

Si on code le prix, charger aussi methodes-numeriques-finance.

Le machine learning de marché charge un skill du tableau. López de Prado, Journal of Portfolio Management, 44(6), 2018 : le backtest est le contrôle de fin. Chaque configuration lancée compte, y compris celles écartées. L'ordre est la série, les traits, l'étiquette, l'importance des variables, l'ajustement, puis ce contrôle.

## Invariants

Le chiffre livre unité, devise, base de jours, calendrier et date de valorisation. La base de jours et le décalage de règlement se lisent sur le contrat et le marché. Actions au comptant américaines : règlement T+1 depuis le 28 mai 2024.

Le cash, les frais et les quantités tiennent en ticks entiers ou en décimal. Le double sert au calcul du prix, avec une tolérance écrite. Deux prix ne se comparent pas avec `==`.

Un prix est une espérance de payoff actualisé, sous une mesure et un numéraire nommés, avec la couverture qui le rend tenable. Sans couverture, on livre une sortie de modèle et ses limites.

Avant un exotique, le même code retrouve un cas fermé : vanille, parité, maturité nulle, vol nulle.

La nappe et la courbe passent leurs tests de non-arbitrage avant d'entrer dans un pricer. Le détail est dans le skill de l'actif.

La série qui sert à décider est celle connue à la date de décision (ml4t-point-in-time). L'univers est la composition publiée à cette date, noms morts compris. Split et dividende sont ceux déjà publiés à cette date.

On n'invente pas un prix, un volume, un Sharpe ou un backtest. Un chiffre sans oracle, sans série citée ou sans sortie fraîche ne sort pas.

## Risque de modèle

Texte en vigueur : guidance interagences du 17 avril 2026, lettre Fed SR 26-2, qui remplace SR 11-7. Elle vise d'abord les banques au-dessus de 30 milliards de dollars. Pour un modèle de prix ou de risque, on en garde le barreau.

Trois pièces. Solidité conceptuelle : conception, hypothèses, données, tests de développement. Analyse des résultats : sorties contre le réalisé, dont le backtest. Suivi : le modèle tient encore quand produits, expositions, données ou marché ont bougé.

La contestation utile vient de quelqu'un qui a la compétence, assez d'indépendance, et le poids pour faire changer le modèle. Un modèle juste employé hors de son usage reste un risque. L'usage, les limites et ce que le modèle ne voit pas s'écrivent à côté du chiffre.

Un modèle de tiers se valide aussi : conception, données, résultats sur les réalisations de la maison. Le code fermé ne dispense pas du backtest.

Un modèle peu matériel se surveille. Un modèle qui porte un prix, un risque ou un capital se valide avant l'usage. Urgence : limites écrites le temps que la validation finisse, et les parties prenantes prévenues des trous.

## Carte MSFE

Tronc commun, lu sur les pages de cours le 2026-10-28. Columbia MSFE, cours requis IEOR E4007, IEOR E4701, IEOR E4703, IEOR E4706, IEOR E4707 et IEOR E4709 : optimisation, modèles stochastiques, Monte-Carlo, fondations, temps continu, séries temporelles. Baruch MFE, 12 crédits requis : marchés (MTH 9814), génie logiciel (MTH 9815), numérique (MTH 9821), probabilités (MTH 9831), capstone (MTH 9903), plus 24 crédits d'électifs (vol, crédit, taux, microstructure, risque, allocation). Berkeley MFE : produits, méthodes empiriques, calcul stochastique, méthodes quantitatives, taux, data science, risque, projet. NYU Courant, sept cours de cœur : marchés, machine learning, calcul stochastique, calcul scientifique, risque et portefeuille, programmation, projet. CMU MSCF, parmi l'année 1 : programmation, simulation (antithétiques, contrôle, échantillonnage préférentiel), calcul stochastique I et II.

Le machine learning s'ajoute à ce tronc. Il ne remplace ni le pricing ni le risque.

QuantNet 2026 (annonce Baruch du 25 novembre 2025) et le guide Risk.net du 18 décembre 2025 mettent Baruch et Princeton en tête. Princeton et le MIT Master of Finance sont des masters de finance, plus larges qu'un MFE. On ne recopie pas les salaires ni les rangs : ils bougent, et ils ne disent pas quoi coder.

## On s'arrête

- Cacher une perte, maquiller un P&L, contourner une limite, peindre un carnet.
- Un backtest qui exécute au mid. Le prix d'exécution est dans microstructure-marche.
- Une covariance échantillon brute inversée dans un optimiseur. Voir portefeuille-quantitatif.
- Un seuil réglementaire recopié de mémoire. Le texte en vigueur se relit (Bâle MAR pour le risque de marché).

## Références

- Columbia, Financial Engineering MS : <https://bulletin.columbia.edu/columbia-engineering/academic-departments-programs/industrial-engineering-operations-research/graduate-programs/financial-engineering-ms/>
- Baruch, curriculum : <https://mfe.baruch.cuny.edu/curriculum/>
- Berkeley MFE : <https://mfe.haas.berkeley.edu/academics/curriculum>
- NYU Courant : <https://math-finance.cims.nyu.edu/academics/>
- CMU MSCF, année 1 : <https://www.cmu.edu/mscf/academics/curriculum/year-one.html>
- Fed, SR 26-2, 17 avril 2026 : <https://www.federalreserve.gov/supervisionreg/srletters/sr2602.htm>
- Guide consolidé : <https://www.federalreserve.gov/frrs/guidance/supervisory-guidance-on-model-risk-management.htm>
- Bâle, MAR33 : <https://www.bis.org/basel_framework/chapter/MAR/33.htm>

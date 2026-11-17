---
name: portefeuille-quantitatif
description: >-
  Allocation, coûts, capacité et Sharpe dégonflé. Use when sizing a book or judging a backtest.
---

# Portefeuille quantitatif

Invariants : finance-quantitative. Fuite d'information : ml4t-lookahead-bias. Jointure datée : ml4t-point-in-time. Régime : ml4t-regime-awareness, pour changer la taille, pas pour sortir du marché sur un label tardif.

La composition de l'univers est celle publiée à la date de décision, noms morts compris (finance-quantitative). Un univers d'aujourd'hui rejoué dans le passé efface les faillites.

## Estimation

L'optimiseur moyenne-variance amplifie l'erreur des entrées (Michaud, Financial Analysts Journal, 1989). On ne l'alimente pas avec la covariance échantillon brute quand le nombre de titres n'est pas petit devant la longueur de l'échantillon.

On rétrécit la covariance vers une cible structurée (Ledoit et Wolf, Journal of Portfolio Management, 2004), ou on contraint avant de chercher un alpha : long only, turnover, levier, exposition de facteur. Quand les titres sont nombreux, le débruitage et l'allocation par grappes sont dans mlp-allocation. Le rétrécissement reste le défaut si l'on inverse encore une matrice.

Une vue partielle se mélange à l'équilibre de marché (Black et Litterman, Financial Analysts Journal, 1992). On n'invente pas un rendement espéré pour chaque titre muet.

## Coûts et capacité

Les coûts sont dans l'objectif : spread, impact, emprunt de titres, frais. Un Sharpe sans coûts est un chiffre de recherche, étiqueté comme tel.

L'impact empirique croît à peu près comme la racine de la participation (Tóth, Lempérière, Deremble, de Lataillade, Kockelkoren, Bouchaud, Physical Review X, 2011). Un coût linéaire sous-estime un gros ordre. La capacité est la taille où le coût mange l'edge. Le backtest d'un petit notionnel n'est pas celui du fonds.

Exécution : le compromis entre risque de délai et impact est nommé (Almgren et Chriss, Journal of Risk, 2001). Une urgence par défaut silencieuse, du type TWAP pour tout ordre, se dit.

Le prix d'exécution et la file d'attente : microstructure-marche.

## Ce qu'on publie

Le Sharpe retenu est souvent le maximum de plusieurs essais. On publie le nombre d'essais. Bailey et López de Prado (Journal of Portfolio Management, 2014) donnent le Sharpe dégonflé, qui corrige la sélection, le surapprentissage du backtest et l'écart à la loi normale. Le seuil, l'asymétrie, l'aplatissement et les essais indépendants se calculent dans mlp-surapprentissage. La probabilité de surapprentissage demande la matrice de tous les essais.

Harvey, Liu et Zhu (Review of Financial Studies, 2016) montrent que le seuil de significativité monte avec le nombre de facteurs déjà essayés dans le catalogue. Un t de 2 après une longue recherche ne se publie pas comme une découverte.

La fréquence et le nombre de points accompagnent le Sharpe. Un Sharpe sur trois mois ne se compare pas à un Sharpe sur dix ans. L'annualisation suppose une forme des rendements. On la nomme.

Le chapitre 14 du livre de 2018 demande, avec le Sharpe, les traits du backtest. Période assez longue pour plusieurs régimes. AUM moyen, longs et shorts en valeur absolue. Levier : taille moyenne en dollars sur cet AUM, avec le coût de l'emprunt. Taille maximale en dollars. Part de paris longs. Nombre de paris par an. Durée moyenne de détention. Un pari finit quand la position est aplatie ou retournée. Compter les allers-retours gonfle le nombre d'occasions. La probabilité qu'une précision fasse rater le Sharpe cible est dans mlp-surapprentissage.

Concentration des rendements de paris, à la façon de Herfindahl. Sur les rendements d'un même signe, au moins trois, la part est le rendement divisé par leur somme. h = (somme des carrés des parts - 1/n) / (1 - 1/n). h vaut 0 si ces rendements sont égaux, 1 si un seul pari porte la somme. Le même indice sur le nombre de paris par mois dit si l'activité est groupée dans le temps. On publie les trois. On cherche des h bas. Le drawdown est la perte maximale entre deux plus-hauts consécutifs du P&L. Le temps sous l'eau va d'un plus-haut jusqu'au dépassement de ce plus-haut. L'attribution par classe de risque se fait sur des partitions disjointes de l'univers. La somme des P&L attribués ne retrouve pas le P&L, les classes se recouvrent.

Levier et vente à découvert : le locate et le rappel ne sont pas dans un backtest qui suppose l'emprunt infini. L'hypothèse d'emprunt est écrite.

## On s'arrête

- Inverser une covariance échantillon sans rétrécissement ni contrainte.
- Un Sharpe de production sans coûts et sans nombre d'essais.
- Juger la capacité sur le notionnel du backtest de recherche.
- Un univers qui ne contient que les noms encore en vie.

## Références

- Michaud, The Markowitz Optimization Enigma, Financial Analysts Journal, 1989.
- Ledoit et Wolf, Honey, I Shrunk the Sample Covariance Matrix, Journal of Portfolio Management, 2004.
- Black et Litterman, Global Portfolio Optimization, Financial Analysts Journal, 1992.
- Bailey et López de Prado, The Deflated Sharpe Ratio, Journal of Portfolio Management, 2014.
- Harvey, Liu, Zhu, and the Cross-Section of Expected Returns, Review of Financial Studies, 2016.
- Almgren et Chriss, Optimal Execution of Portfolio Transactions, Journal of Risk, 2001.
- Tóth et al., Anomalous Price Impact and the Critical Nature of Liquidity in Financial Markets, Physical Review X, 2011.
- López de Prado, Advances in Financial Machine Learning, Wiley, 2018, chapitre 14.

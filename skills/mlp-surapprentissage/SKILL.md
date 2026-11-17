---
name: mlp-surapprentissage
description: >-
  Sharpe dégonflé, PBO, nombre d'essais. Use when a backtest Sharpe is about to be trusted or compared.
---

# Surapprentissage du backtest

Invariants : finance-quantitative. Ce qu'on publie à côté du Sharpe (coûts, fréquence, univers) : portefeuille-quantitatif. Les chemins : mlp-validation.

López de Prado, Journal of Portfolio Management, 44(6), 2018, piège 10. Le backtest est le contrôle de fin. Il ne sert pas à chercher une idée. La deuxième loi du livre de 2018 : on ne cherche pas sous l'influence d'un backtest. S'il échoue, on reprend au début. On ne recolle pas le modèle sur ce résultat. La troisième loi : tout résultat se publie avec tous les essais qui l'ont produit.

Chaque configuration lancée compte, y compris celles écartées et celles d'autres auteurs sur les mêmes données. Sans ce nombre, le Sharpe ne s'interprète pas. Un backtest sans fuite, aux coûts larges, reste probablement faux dès qu'il est le survivant de beaucoup d'essais. C'est l'objet du Sharpe dégonflé et de la PBO. Les scénarios, par la validation combinatoire (mlp-validation) ou par des chemins synthétiques (mlp-etiquetage), remplacent le seul chemin historique.

Le paradigme méta-stratégie sépare les tâches (López de Prado, Practical Applications, 2014). Pour un auteur seul, la séparation est l'ordre : les variables se jugent avant ce contrôle, et un backtest déjà vu ne se retouche pas sans incrémenter le nombre d'essais.

## Sharpe probabiliste et dégonflé

Le Sharpe de la formule est celui de la fréquence des rendements, pas un Sharpe annualisé. T est le nombre de rendements. L'asymétrie γ3 et l'aplatissement γ4 sont ceux des rendements. γ4 vaut 3 pour une loi normale. Un aplatissement excédentaire (0 pour la loi normale) fausse le seuil.

Bailey et López de Prado, Journal of Risk, 2012. Le Sharpe probabiliste est la probabilité que le vrai Sharpe dépasse un seuil SR*, pour un Sharpe observé SR :

PSR(SR*) = Φ( (SR - SR*) √(T - 1) / √(1 - γ3 SR + ((γ4 - 1) / 4) SR²) )

Φ est la fonction de répartition de la loi normale centrée réduite.

Bailey et López de Prado, Journal of Portfolio Management, 2014. Le Sharpe dégonflé est ce PSR dont le seuil n'est plus choisi. N est le nombre d'essais indépendants. V est la variance des Sharpe de ces essais. γ est la constante d'Euler-Mascheroni, environ 0,5772156649.

SR* = √V × ( (1 - γ) Φ⁻¹(1 - 1/N) + γ Φ⁻¹(1 - 1/(N e)) )

Si les essais sont très corrélés, le N brut surestime la peine quand on le traite comme indépendant. On estime alors un N d'essais indépendants, ou on passe à la PBO, qui ne demande pas cette hypothèse. Si le Sharpe observé est déjà sous SR*, allonger la piste ne le fait pas franchir ce seuil.

La longueur minimale de backtest, pour qu'un Sharpe donné ne soit pas le maximum attendu de N essais sans edge, est dans Bailey, Borwein, López de Prado et Zhu, Notices of the American Mathematical Society, 61(5), 2014. On ne la recalcule pas de mémoire.

## Probabilité de surapprentissage

La PBO a besoin de la matrice des rendements de tous les essais, gagnants et perdants. Bailey, Borwein, López de Prado et Zhu, Journal of Computational Finance, 2017. La validation combinatoire symétrique coupe les lignes en un nombre pair de blocs. Chaque moitié des blocs sert à son tour d'échantillon de sélection, le complément sert de test. La PBO est la part de ces découpes où l'essai gagnant en sélection est sous la médiane hors sélection. Au-dessus de un demi, la procédure de sélection retient plus souvent un essai surajusté.

Un Sharpe publié sans N, et sans cette matrice, ne donne ni DSR ni PBO.

Le seuil de significativité qui monte avec le catalogue de facteurs déjà essayés est dans portefeuille-quantitatif (Harvey, Liu et Zhu, 2016). On ne le recopie pas.

## Risque de la stratégie

Ce Sharpe-ci ne passe pas par les rendements. Il part de la précision p des paris et de leur gain. Il ne se mélange pas au PSR : le PSR teste un Sharpe de rendements, avec asymétrie et aplatissement. Ici, le gérant choisit les gains et le nombre de paris. Le marché fixe p.

Paris symétriques de taille π. Le Sharpe annualisé vaut (2p - 1) / √(p (1 - p)) × √n / 2. π disparaît. C'est un t de p contre un demi, remis à l'échelle. n est le nombre de paris par an. Exemples du livre, pas des cibles : p = 0,55 demande 396 paris par an pour un Sharpe de 2. À 52 paris, il faut p proche de 0,6336 pour le même Sharpe.

Paris asymétriques, gain π+ et perte π-. Le Sharpe vaut ((π+ - π-) p + π-) / ((π+ - π-) √(p (1 - p))) × √n. L'exemple du livre, n = 260, π- = -0,01, π+ = 0,005 : p = 0,7 donne un Sharpe proche de 1,17, p proche de 0,72 donne 2, p = 0,67 efface le profit, et p sous 2/3 donne un Sharpe négatif ou nul. Un petit écart de p bouge le Sharpe fortement.

La probabilité d'échec est P[p < p*], où p* est la précision qui atteint juste le Sharpe cible. On estime π+ et π- sur la série des issues, ou par un mélange de deux gaussiennes. n est le nombre de paris divisé par le nombre d'années. On bootstrap la précision sur l'horizon de l'investisseur. L'exemple du livre prend deux ans. On intègre ensuite la densité sous p*. Pour un horizon long, l'approximation normale p(1 - p) / T est admise. La règle de mise en production du livre écarte la stratégie si cette probabilité dépasse 0,05, même sur un titre calme. 0,05 s'écrit avant. Ce n'est pas une constante du marché.

## On s'arrête

- Annoncer un Sharpe sans le nombre d'essais.
- Annualiser le Sharpe avant de l'entrer dans le PSR.
- Prendre γ4 = 0 pour une loi normale dans cette formule.
- Calculer une PBO sur le seul gagnant.
- Relancer le backtest pour améliorer le résultat, puis publier le dernier essai comme s'il était le premier.
- Lire le Sharpe déduit de la précision des paris comme un PSR.
- Recopier 396 paris, ou le seuil 0,05, comme une loi.

## Références

- Bailey et López de Prado, The Sharpe Ratio Efficient Frontier, Journal of Risk, 15(2), 2012.
- Bailey et López de Prado, The Deflated Sharpe Ratio, Journal of Portfolio Management, 40(5), 2014.
- Bailey, Borwein, López de Prado et Zhu, Pseudo-Mathematics and Financial Charlatanism, Notices of the AMS, 61(5), 2014.
- Bailey, Borwein, López de Prado et Zhu, The Probability of Backtest Overfitting, Journal of Computational Finance, 2017.
- López de Prado, Quantitative Meta-Strategies, Practical Applications, 2(3), 2014.
- López de Prado, Advances in Financial Machine Learning, Wiley, 2018, chapitres 11, 14 et 15.

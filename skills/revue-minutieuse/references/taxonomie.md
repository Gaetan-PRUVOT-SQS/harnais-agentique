# Taxonomie du code mort

Référence de `revue-minutieuse`. Une classe suffit pour un bloquant. On
déduplique par symbole, pas par fichier.

Le code mort est un indice de logique fausse, pas seulement du bruit.
CWE-561, CERT MSC07-C / MSC56-J, MISRA C Rule 2.2. L'inatteignable a déjà
fait sauter une vérif (Apple `goto fail`, CVE-2014-1266).

## Classes

| Classe | Forme | Preuve |
|---|---|---|
| Inatteignable | Après `return` / `throw` / `break` sans condition, `goto` inconditionnel, `if` dont le prédicat est impossible sur tous les chemins qui y arrivent | Un chemin concret jusqu'au bloc, puis aucun successeur qui l'exécute |
| Inutilisé | Import, variable, paramètre, fonction, type, export, fichier, dépendance déclarée jamais lus | Aucun appelant dans le graphe du projet, hors entrée documentée (CLI, plugin, test, réflexion nommée) |
| Sans effet | Expression calculée, résultat jeté ; assignation jamais lue ; incrément dont la valeur disparaît | MISRA 2.2. Un `(void)` ou un discard explicite du langage, pour un retour qu'on **doit** ignorer, reste vivant s'il est expliqué |
| Commenté | Code en commentaire, `#if 0`, `if False:` autour d'une implémentation | Interdit par AGENTS.md. On retire, on ne réactive pas plus tard |
| Spéculatif | Branche, option, type, couche, helper pour un besoin absent du critère | Google, over-engineering. YAGNI : `pratiques-agiles` |
| Doublon | Même travail qu'un symbole déjà dans le dépôt | Recherche du nom et du comportement avant d'ajouter |
| Désactivé | Feature flag jamais allumé, test sauté, handler jamais enregistré | Lens 12 de `code-review/references/correctness-taxonomy.md` (atteignabilité) |
| Debug | `console.log`, `print`, dump, timer de mesure laissés | Hors critère de diagnostic demandé |
| Pass-through | Fonction ou fichier qui ne fait que déléguer, sans invariant | Test de suppression : si on l'ôte, la complexité disparaît |
| Valeur morte | Champ, clé de config, constante jamais lue ; résultat stocké puis écrasé sans lecture | Suivre les lectures, pas les écritures |

Une couverture nulle n'égale pas du code mort : ça peut être un cas de test
manquant (`iso-29119`). Un code mort a souvent une couverture nulle. On
tranche avec les trois questions, pas avec le seul chiffre.

## Faux positifs fréquents

À vérifier avant de déclarer mort :

- Point d'entrée hors import : `main`, script CLI, hook, plugin, URL de
  framework, table de syscalls, symbole exporté pour un autre langage
- API publique d'une bibliothèque : le dépôt est le producteur, les
  appelants sont dehors. Une exportation publique **nouvelle** reste
  exigée par le critère, sinon elle ne part pas
- Réflexion, dispatch par nom, `dlsym`, attributs de sérialisation
- Tests qui importent le symbole ; lancer l'outil aussi sur la suite
- Code généré relu par un outil qui ignore le générateur

Un doute se tranche vers « vivant » seulement avec un appelant nommé
(`fichier:ligne` ou contrat public écrit). Sinon on retire.

## Périmètre

Dans le diff : retirer.

Hors du diff, déjà là : signaler en note, ne pas élargir le commit.
Exception : le changement vient de rendre le symbole inutilisé, alors il
sort dans ce diff.

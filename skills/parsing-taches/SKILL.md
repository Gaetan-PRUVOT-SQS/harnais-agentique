---
name: parsing-taches
description: >-
  Algo de parsing de lots pour grappe hétérogène (edge, volunteer, HTC) :
  IR de description séparée de l'ordonnanceur, infer-then-validate,
  estimate/bound/request, charge, oracle de vérif. Use when writing or
  changing a task parser, parseWorkload, moteur de parsing, ClassAd, JSDL,
  CWL ResourceRequirement, BOINC workunit, HEFT rank, claim par poids,
  lots sha256/llm, Datagrappler parse, or /parsing-taches.
---

# Parsing de tâches

Quand on écrit ou on change un parseur de lots pour une grappe
hétérogène (téléphones, PCs, nœuds volunteer). Le parseur rend une IR
que l'ordonnanceur consomme. Appliquer au code seulement si la demande
nomme le parseur ou le projet.

Voisins : `pratiques-agiles` (champs lus par cet incrément),
`revue-minutieuse` (aucune ligne morte), `iso-29119`,
`norme-cybersecurite` (entrée utilisateur à la frontière).

## Invariant

Le parseur décrit le travail. L'ordonnanceur le place. Deux modules,
deux contrats. Une fonction `parseWorkload` (ou équivalent) rend une IR
ou refuse. Elle ne choisit pas le nœud.

## Pipeline

Ordre fixe. Une étape qui échoue refuse le lot entier.

1. **Frontière.** Schéma du lot : cardinalité, taille max par payload,
   encodage. Échec → refuse (400 / null), rien n'est persisté.
2. **Kind.** Type explicite s'il est fourni. Sinon inférer : la forme
   la plus spécifique qui couvre **tous** les payloads. Hex pair avant
   texte libre. Aucune forme unique → refuse. Un lot mixte refuse.
3. **Valider.** Chaque payload contre le schéma du kind. Type explicite
   n'autorise pas un payload hors schéma. Normaliser ici (casse, trim,
   fins de ligne) et garder la forme canonique.
4. **IR de tâche**, un enregistrement par payload, seulement les champs
   qu'un lecteur existe déjà (claim, complete, SPA, résumé) :

   | Champ | Sert à | Lecteur typique |
   |---|---|---|
   | `kind` | choisir l'exécuteur et l'oracle | claim, agent, complete |
   | `payload` | le travail | agent |
   | `estimate` (poids) | classer, ETA | `ORDER BY` du claim |
   | `bound` | abort / plafond d'exécution | complete, watchdog |
   | `request` | filtre dur de nœud | `WHERE` du claim |
   | `charge` (`light` / `heavy`) | résumé humain, classes de taille | SPA, compteurs |
   | `verify` | nom de l'oracle | complete |
   | `bytes_transfer` | CCR | claim, si on compare au poids |

5. **Sortie.** `Workload { kind, tâches[], résumé }`. Le résumé (light,
   heavy) se calcule sur l'IR, il ne se saisit pas à part.

## Trois nombres distincts

Ils ne se recopient pas l'un dans l'autre.

| Nombre | Question | Si on le manque |
|---|---|---|
| `estimate` | Combien ça coûte, pour classer ? | L'ordre du claim devient FIFO, les gros lots bloquent les petits |
| `bound` | Au-delà de quoi on abort ? | Un nœud coincé garde le lot |
| `request` | Quel nœud a le droit de le prendre ? | On envoie un lot plus gros que la RAM du téléphone |

Sources de ces trois cases : BOINC `rsc_fpops_est` / `rsc_fpops_bound` /
`rsc_memory_bound` ; CWL `min` (ne pas lancer) / `max` (plafond
d'allocation) ; Kubernetes `requests` (placement) / `limits` (plafond
runtime) ; HTCondor `Requirements` (filtre booléen) / `Rank` (préférence).

Un `estimate` sert au classement, un `bound` à l'abort. Un nœud refuse
un lot dont le `request` dépasse sa capacité **avant** de le recevoir.

## Annonces symétriques

Deux fiches, match dans les deux sens (ClassAds) :

- **Tâche** : kind, payloads, estimate, bound, request, verify.
- **Nœud** : capacités (RAM, batterie, charge actuelle), préférence de
  claim (`light` prend le plus petit poids, `heavy` le plus grand).

L'énergie, la thermique et la batterie vivent sur la fiche nœud. Elles
passent sur la fiche tâche seulement si le job a son propre budget
(deadline, joules). Un parseur n'invente pas un champ CPU / arch /
stockage / thermique tant que claim, complete ou la SPA ne le lisent pas.

## Inférer puis valider

Table de décision, à coller dans les tests :

| Type fourni | Forme des payloads | Sortie |
|---|---|---|
| `sha256` / `llm` / … | tous valides pour ce kind | ce kind, payloads canoniques |
| `sha256` / `llm` / … | un payload hors schéma | refuse |
| absent | tous hex pairs valides | `sha256` (forme la plus spécifique) |
| absent | tous textes valides, au moins un hors hex pair | `llm` |
| absent | mixte, vide, hors schéma | refuse |

La forme la plus spécifique gagne. Un hex pair est aussi un texte : on
teste l'hex **en premier**. Un type explicite gagne sur l'inférence, et
chaque payload doit encore passer le schéma.

## Lots indépendants

Par défaut, lots HTC indépendants (BOINC). Le rang HEFT d'une tâche
sans successeur se réduit à son coût moyen : c'est l'`estimate`.

`rang_u(n_i) = w_moy(i) + max_succ (c_moy(i,j) + rang_u(n_j))`. Nœud
de sortie : `rang_u = w_moy`. On n'écrit cette formule dans le parseur
que si le lot a des **arcs** et que l'ordonnanceur lit le rang.

CCR = coût moyen de transfert / coût moyen de calcul. Si le transfert
dépasse le calcul, l'ordonnanceur garde le lot groupé, ou le refuse.
Le parseur émet `bytes_transfer` seulement si le claim compare ce
chiffre au poids.

Classes de taille (BOINC MultiSize) : gros lots vers nœuds lourds,
petits vers légers. Si nœud et tâche dépareillent, garder la tâche
plus légère.

## Oracle nommé à l'analyse

Le parseur pose le nom de l'oracle sur l'IR. `complete()` le rejoue.

| Kind | Oracle | Échec |
|---|---|---|
| digest (sha256, hash) | recalcul côté relais, comparaison stricte | `bad_output`, requeue |
| extract (llm extractif) | même fonction, mêmes constantes, côté relais | `bad_output`, requeue |
| volunteer non fiable | quorum / réplication (BOINC) | désaccord, requeue |

Nœuds non fiables : le relais recoupe. Un parseur qui oublie `verify`
laisse `complete()` inventer la règle.

## Instance v1 (Datagrappler)

Mapping actuel. Un champ nouveau entre seulement si le prochain
incrément a un lecteur.

| Règle du skill | Code actuel |
|---|---|
| Kind | `sha256` \| `llm` |
| Inférence | tous hex pairs → `sha256` ; sinon tous prompts → `llm` ; sinon `null` |
| `estimate` | `llm` → 0 ; `sha256` → `length(payload_hex)` (`TASK_WEIGHT_SQL`) |
| `charge` | `llm` → `light` ; `sha256` → `heavy` si longueur ≥ `HEAVY_SHA256_HEX` (8192) |
| `verify` | digest / extract (`orchestrator/src/llm.ts`, rejeu au complete) |
| `bound`, `request`, `bytes_transfer` | absents : claim ne les lit pas |
| Lots | indépendants, 1-256 payloads |
| Nœud | `nodeScore = ramMb * 100 + batteryPct` ; batterie < 20 % ou sous la médiane → light |

Le seuil 8192 sert au résumé (`light` / `heavy`). Le claim reste
continu sur le poids : `aa` passe avant `aabbcc` chez un nœud light.

## Quand on change le parseur

Avant d'ajouter un champ : nommer le lecteur (`claim` SQL, `complete`,
SPA, agent). Sinon on n'écrit pas le champ.

Le parseur et le SQL de claim restent jumeaux : un poids calculé en
TypeScript et un `ORDER BY` qui dit autre chose, c'est un incident.

Entrées : Zod (ou équivalent) à la frontière HTTP, puis
`parseWorkload`. L'agent ne revalide pas un schéma déjà tranché par le
relais, sauf oracle de sortie.

## Tests

Base de test : ce skill, plus le schéma du projet.

| Modèle | Technique | Cas minimum |
|---|---|---|
| Type fourni / inféré / mixte | table de décision | les cinq lignes ci-dessus |
| Cardinalité | valeurs limites | 0, 1, 256, 257 |
| Taille payload | valeurs limites | 0, 1, max, max+1 |
| Hex pair vs texte | partitions | `aa`, `abc`, `'  '`, mixte |
| Poids | partitions + limites | `llm` → 0 ; `aa` < `aabb` ; seuil de charge |
| Oracle | confirmation | sortie fausse → `bad_output` ; sortie juste → done |

Un test du parseur reste vert si on casse le claim : ajouter le cas
d'intégration (ordre light / heavy). Couverture du module parseur ≥ 90 %
lignes et branches (`iso-29119`).

## On s'arrête

- Le parseur choisit le nœud, ou le claim recalcule un kind.
- Un champ CPU, arch, stockage, thermique, DAG, HEFT, sans lecteur.
- Recopier du JSDL XML, une ClassAd HTCondor, un manifeste CWL.
- Un `estimate` collé dans `bound` « pour simplifier ».
- Un lot mixte accepté, un type explicite qui laisse passer un hors schéma.
- Un oracle seulement côté agent, jamais rejoué au relais.

## Sources

- HTCondor ClassAds : `Requirements` (filtre) et `Rank` (préférence),
  fiches job et machine, matchmaker.
  https://htcondor.readthedocs.io/en/latest/misc-concepts/classad-mechanism.html
- JSDL GFD-R.056 : description de soumission (ressources, limites,
  staging). L'état d'exécution est un autre document.
  https://www.ogf.org/documents/GFD.56.pdf
- CWL `ResourceRequirement` : `min` insatisfait → ne pas lancer ;
  `max` = plafond d'allocation. L'engin place, le langage décrit.
  https://www.commonwl.org/v1.2/CommandLineTool.html#ResourceRequirement
- Kubernetes QoS : `requests` / `limits`, Guaranteed / Burstable /
  BestEffort. CPU throttle, mémoire OOMKill.
  https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/
- BOINC workunit : `rsc_fpops_est`, `rsc_fpops_bound`,
  `rsc_memory_bound`, `rsc_disk_bound` ; classes de taille ; nœuds
  non fiables (quorum).
  https://boinc.berkeley.edu/trac/wiki/JobIn
- HEFT, Topcuoglu, Hariri, Wu, IEEE TPDS 2002 : `rank_u`, CCR.
  Independent tasks → le rang se réduit au coût moyen.
- MEC / edge 2024-2026 : tâches hétérogènes, batterie et thermique
  sur la fiche nœud.

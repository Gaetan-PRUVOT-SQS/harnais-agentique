## Tests

Base de test : <critères d'acceptation, sujet, spec, page de manuel>

### Risques

| Risque | Impact (1 à 3) | Probabilité (1 à 3) | Réponse de test |
|--------|----------------|---------------------|-----------------|
| | | | |

### Conception

| Modèle de test | Technique | Éléments de couverture | Cas (fichier : nom) |
|----------------|-----------|------------------------|---------------------|
| | | | |

- Niveaux : <composant, intégration, système, acceptation>
- Types (ISO/IEC 25010) : <fonctionnel, sécurité, performance...>
- Couverture visée : au moins 90 % sur chaque couverture rapportée
  (lignes ou instructions, branches, issues de conditions si l'outil
  les donne). Le risque élevé peut exiger plus.
- Critères de fin : <tous les cas verts, couverture atteinte, aucun
  incident grave ouvert, check sécu OK>

### Résultat

- Date, commit, commande :
- Cas : <passés> sur <total> ; couverture atteinte :
- Incidents : <identifiant, gravité, statut, test de régression>
- Écarts au plan, risques résiduels :

---

# Exemple rempli (droits d'accès, `iso-29119/exemples`)

## Tests

Base de test : règle d'accès de type Unix de fichiers-unix (classe
propriétaire, puis groupe, puis autres ; root passe tout sauf l'exécution
sans aucun bit x) ; mode limité à 0777, demande de 1 à 7.

### Risques

| Risque | Impact (1 à 3) | Probabilité (1 à 3) | Réponse de test |
|--------|----------------|---------------------|-----------------|
| Accès donné à tort (fuite, élévation) | 3 | 2 | table de décision complète, MC/DC 100 % |
| Entrée hors domaine acceptée | 3 | 2 | valeurs limites sur mode et demande |
| Classe mal choisie (propriétaire aussi du groupe) | 2 | 2 | supposition d'erreur |

### Conception

| Modèle de test | Technique | Éléments de couverture | Cas (fichier : nom) |
|----------------|-----------|------------------------|---------------------|
| M1 domaine du mode (limite 0777) | valeurs limites (2 valeurs) | 0777, 01000 | `test_acces.c` : limite mode 0777 valide, limite mode 01000 invalide |
| M2 domaine de la demande (1 à 7) | valeurs limites (2 valeurs) | 0, 7, 8 | limite voulu 0, 7, 8 |
| M3 règle root et exécution | table de décision, MC/DC | 4 règles root, 2 conditions | table root lit, écrit, exécute sans bit x, avec un bit x |
| M4 choix de la classe | table de décision | 6 règles | table propriétaire, groupe, autre |
| M5 bits demandés présents ou non | partitions | tous présents, un manquant | partition tous les bits voulus, un bit manquant |
| M6 propriétaire aussi membre du groupe | supposition d'erreur | 1 cas | erreur proprietaire aussi du groupe |

- Niveaux : composant (hôte).
- Types : fonctionnel, sécurité.
- Couverture visée : lignes, branches et issues de conditions à 100 %.
- Critères de fin : 18 cas verts sous ASan et UBSan, `make couverture`
  vert, `bats tests` vert.

### Résultat

- 2026-09-29, `make verifier` (gcc 16.2.1).
- Cas : 18 sur 18 ; lignes 100 % de 15, branches 100 % de 16, issues de
  conditions 100 % de 16.
- Preuve du seuil : sans le cas « root exécute avec un bit x », branches
  et conditions tombent à 93,75 % et `make couverture` échoue.
- Risques résiduels : bits setuid, setgid et sticky hors du domaine
  (refusés) ; listes de contrôle d'accès non traitées.

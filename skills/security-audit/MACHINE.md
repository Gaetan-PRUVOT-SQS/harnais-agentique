# Harnais local

Ce fichier prime sur le reste du skill. `~/.agents/AGENTS.md` prime sur ce fichier.

Source : https://github.com/cloudflare/security-audit-skill, commit `c1c8a8c1471069fb0e188eeaff69b8e8db6564a8`, licence MIT (`LICENSE`).

## Place

Dossier canonique : `~/.agents/skills/security-audit`. Grok lit `~/.agents/skills` directement.

## Modes

Le mode guidé est le défaut. Question, revue ciblée, triage : seulement les parties utiles. Pas de dossier de sortie, pas des six phases.

L'audit complet ne démarre que si l'auteur demande un audit, un pen-test, une revue complète, ou des rapports. Une question de sécurité ne suffit pas.

## Délégation

Un seul niveau. Le parent est la session courante. Il est le seul à écrire les fichiers partagés du run. Pas de worktree, pas de copie du dépôt.

Mode guidé :

- revue d'un flux : `auditeur-securite`
- carte du code : `explorateur`
- question avec sources : `chercheur`

Ces agents rendent un rapport court. Ils ne suivent pas le format chasseur du skill.

Audit complet : sous-agent général (sans `subagent_type`), brief du skill, lecture seule. `auditeur-securite` plafonne le rapport et impose un autre format, donc il ne porte pas les vagues de chasse. Le brief interdit d'écrire, de committer et de pousser. Après chaque retour, le parent vérifie que l'arbre de la cible n'a pas bougé.

## Exécution

Le bac à sable demandé (réseau coupé, environnement vide, cible en lecture seule, limites CPU et disque) n'est pas en place ici. Ne pas lancer le build, les tests, un binaire, un émulateur ou un fuzzer de la cible. Le lead reste `needs_validation`, avec le fait qui manque et un plan de contrôle sûr.

Pas de `/tmp`. Pas de copie du projet pour essayer du code.

## Sortie

Audit complet : `~/security-audit-skill/<nom-du-dépôt>/run-<N>`, hors du dépôt cible. Écrire dans le dépôt seulement si l'auteur désigne un dossier et que git ignore ce dossier en entier.

## Portes déjà là

`norme-cybersecurite`, `security-gate` et `revue-validation` restent les portes de livraison. Ce skill ne les remplace pas. Il ne modifie pas le code de la cible et il ne commit pas.

## Validateur

Depuis ce dossier : `make test`, ou `node validate-findings.cjs` et `node validate-coverage-ledger.cjs` sur les JSON du run. Node est déjà là. Aucune dépendance à installer.

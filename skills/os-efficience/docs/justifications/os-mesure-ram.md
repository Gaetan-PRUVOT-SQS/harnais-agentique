# Feature : os-mesure ram, RAM minimale mesurée

Date : 2026-09-29

## Métier

- Besoin : VelumOS promet d'être frugal et vise de vieux PC. La RAM minimale
  est un chiffre de la promesse, et `RAM_MIN` du `make test` doit venir
  d'une mesure, pas d'une estimation.
- Qui est concerné : L'auteur quand il fixe ou relève le budget RAM, le
  harness de test qui garde ce budget.
- Impact si on ne le fait pas : `RAM_MIN` choisi au jugé, régression de
  RAM invisible jusqu'au jour où une vieille machine ne démarre plus.

## Ce qu'on fait

- Comportement visible : `os-mesure ram kernel.elf [--max 64] [--budget N]`
  démarre QEMU avec `-m N` en Mio, cherche par dichotomie la plus petite
  valeur où le marqueur série apparaît, affiche chaque essai, la RAM
  minimale et le nombre de démarrages. Code 1 si le budget est dépassé ou
  si le marqueur n'apparaît pas même avec `--max`.
- Fichiers touchés : `scripts/os-mesure` (`marqueur_vu`, `demarre_avec`,
  `plus_petit_qui_passe`, `cmd_ram`), `scripts/test_os_mesure.py`,
  `scripts/fixtures/serie-*.log`, `scripts/pyproject.toml`.

## Choix techniques

| Choix | Pourquoi | Alternative rejetée | Impact métier |
|-------|----------|---------------------|---------------|
| Dichotomie de 1 à `--max` Mio | 64 Mio en 7 démarrages au plus | essayer chaque valeur | mesure en quelques secondes, lançable souvent |
| Vérifier `--max` d'abord | un marqueur absent n'est pas une « RAM minimale de 64 » | dichotomie directe | pas de faux chiffre |
| Sortie série dans `build/mesure/ram.log` | même règle que `profil` : tout reste dans le projet | fichier temporaire | conforme à tests-locaux |
| Arrêt dès le marqueur, délai par essai (`--secondes`) | le noyau s'arrête sur `hlt` sans quitter QEMU | attendre la fin de QEMU | un essai prend moins d'une seconde quand il réussit |
| Monotonie supposée (si N démarre, N+1 aussi) | vraie pour un noyau qui ne dépend que de la taille de RAM | tout balayer | assumée et écrite ici ; un résultat surprenant se vérifie à la main |
| `plus_petit_qui_passe` pure, testée | la logique se teste sans QEMU | tester seulement en vrai | tests en 0,1 s |

## Traçabilité

| Fichier | Fonction / bloc | Justifié par |
|---------|-----------------|--------------|
| `scripts/os-mesure` | `plus_petit_qui_passe` | dichotomie |
| `scripts/os-mesure` | `cmd_ram` (essai de `--max`) | vérifier `--max` d'abord |
| `scripts/os-mesure` | `demarre_avec`, `marqueur_vu` | sortie série, arrêt dès le marqueur |
| `scripts/test_os_mesure.py` | tous | logique pure testée |

## Notes

Mesuré le 2026-09-29 sur le gabarit osdev-c (release) : 2 Mio en
7 démarrages, 1 Mio ne démarre pas. Même chiffre que l'ancienne mesure de
VelumOS.

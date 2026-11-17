# Harnais agentique

Un harnais de travail complet pour agents de code : règles permanentes,
garde-fous exécutés en hooks, 202 skills, 5 sous-agents en lecture seule,
et un verifier qui contrôle l'ensemble à chaque fin de tour. Conçu pour
qu'un agent de code travaille de façon fiable : ce qu'il affirme est
prouvé, ce qu'il casse est bloqué, ce qu'il livre est vérifié.

## Principes

- **La preuve, pas le récit.** Chaque affirmation s'appuie sur une sortie
  fraîche (`fichier:ligne`), jamais sur le compte rendu d'un agent. Un
  reçu par critère = un oracle indépendant du code + une sortie relue.
- **Un seul écrivain.** Les sous-agents lisent et rendent un rapport ; le
  fil principal écrit, puis revérifie chaque rapport avec une preuve
  neuve. Jamais deux écrivains sur un même dépôt.
- **Les règles sont tenues par la machine.** Des gates branchées sur les
  événements de l'agent bloquent la fin de tour si un contrôle échoue.
  Un Stop vert ne tient pas lieu de validation : il couvre le scan sécu
  et la suite de régressions reconnue.
- **Une seule source de vérité.** Les règles vivent dans `AGENTS.md` et
  `regles/`, nulle part ailleurs. Les skills, hooks et mémoires ne les
  répètent pas : ils y renvoient.
- **La mémoire ne contient que des faits.** Les faits durent (poste,
  projets, écosystème) ; une règle ne s'écrit jamais dans la mémoire.
- **Le contexte est une ressource finie.** Le listing des skills est
  budgété et mesuré (plafond contrôlé par le verifier) ; on charge à la
  demande.

## Méthode de travail (résumé d'AGENTS.md)

- **Mode auto** : l'agent tranche les choix par défaut et avance ; il
  s'arrête seulement pour perte de données irréversible, publication,
  secret manquant ou garde-fou bloquant. Un critère mesurable est fixé
  avant d'agir.
- **Niveau senior partout** : une tranche fonctionnelle à la fois, YAGNI,
  pas de code mort, pas de commentaires dans le code (les choix se
  justifient en privé, par écrit, un document par décision).
- **Pipeline immuable** : feature → tests d'intégration + régressions →
  correction si échec → validation → **commit local** (staging fichier
  par fichier, message court et naturel). Jamais de push sans demande.
- **C** : `gcc -Wall -Wextra -Werror`, zéro fuite mémoire prouvée, shell
  strict (`set -eu`, shellcheck, checkbashisms, shfmt).
- **Tests** : ISO/IEC/IEEE 29119, couverture ≥ 90 % (MC/DC sur le code à
  risque), preuve fraîche exigée, jamais de résultat inventé.
- **Sécurité** : baseline + OWASP sur le flux touché ; audit complet si
  auth, données personnelles ou paiement.
- **Git** : identité stable par l'environnement, messages courts sans
  préfixes ni trace d'outil, un commit par feature embarquant ses
  régressions.

## Structure

```
AGENTS.md            règles permanentes (méthode, git, tests, mémoire)
regles/bas-niveau.md règles additionnelles OS / noyau / pilotes :
                     spec matériel citée, preuve par paliers (hôte,
                     QEMU, vraie machine), invariants kassert, budget
                     mémoire écrit, ABI versionnée
DESIGN.md            contrat visuel par défaut de toute UI (palette,
                     polices par rôle, défauts interdits, revue par
                     capture d'écran réelle)
skills/              202 skills au format SKILL.md (frontmatter
                     name + description ≤ 1024 caractères)
agents/              5 sous-agents lecture seule
hooks/               dispatch.py (entrée unique) + garde + gates
verifier             contrôle la config entière (voir plus bas)
tests/               suite pytest du harnais (187 tests)
.skill-lock.json     provenance et empreinte des skills importés
```

## Les skills (202)

Piles couvertes, par priorité : bas niveau (C, OS, assembleur, noyau,
libc, shell maison), réseau (pile, microstructure), Android (Compose,
performance, sécurité, CI), WordPress (plugins, thèmes, REST),
CI/CD (GitHub Actions, Docker), GCP, Postgres, et finance quantitative
(pricing, dérivés, revenu fixe, risque, portefeuille, ML appliqué aux
marchés avec garde-fous anti-fuite de données). Plus l'outillage transverse :
TDD, revue minutieuse ligne à ligne, audit sécurité, vérification par
preuve. Chaque skill importé est tracé dans `.skill-lock.json` (source,
empreinte) ; les skills maison sont en français.

## Les agents (5, lecture seule)

| Agent | Rôle |
|---|---|
| `architecte` | plan d'implémentation : étapes, dépendances, fichiers critiques, compromis |
| `auditeur-securite` | audit OWASP ciblé sur le flux touché, gravités, `chemin:ligne` |
| `chercheur` | recherche profonde code/web avec chaîne de preuves |
| `explorateur` | exploration de dépôt, résumé avec `chemin:ligne` |
| `relecteur` | relecture de diff à contexte vierge, défauts de correction |

Aucun sous-agent n'écrit : ils rendent un rapport (≤ 2 000 tokens) que le
fil principal revérifie.

## Les hooks

Entrée unique : `dispatch.py`, appelé avec l'événement en argument. Tout
le reste (garde, gates) est routé par lui — aucun hook ailleurs.

| Événement | Ce qui tourne | Effet |
|---|---|---|
| `PreToolUse` | garde : secrets, `rm` récursif, écriture disque, firmware, force-push | `deny` / `ask` avant l'action |
| `PostToolUse` (écritures) | shellcheck, checkbashisms, format (shfmt/ruff), scan cyber | blocage si échec |
| `Stop` | scan cyber, tests de régression, oracle, verifier de config | la main ne revient pas tant qu'un contrôle échoue |
| `SessionStart` / `UserPromptSubmit` | état de session, déclencheurs ponctuels | nettoyage, aiguillage |

Le garde traduit les noms d'outils du moteur hôte (Grok, Claude Code,
ZCode) vers un vocabulaire commun.

## Le verifier

```sh
./verifier --rapide    # ~30 s, lancé par la gate Stop si la config a changé
./verifier             # complet, avant de clore un chantier
```

Contrôles : frontmatter et liens des 202 skills et 5 agents, budget du
listing, hooks en python isolé (`python3 -E -s`, délais exacts), refus de
secrets, gitleaks, semgrep, ruff, shellcheck, checkbashisms, suite pytest
complète. Les contrôles liés au poste (moteur branché, outillage installé)
passent en « non lancés » si le fichier visé est absent : le dépôt est
vert sur toute machine.

## Installation

```sh
git clone <ce dépôt> ~/.agents
~/.agents/verifier --rapide
```

Puis brancher votre moteur — un moteur par copie, jamais deux écrivains
sur le même dépôt :

**Règles** : lier `AGENTS.md` dans les instructions du moteur.

**Skills et agents** : liens symboliques (beaucoup de moteurs découvrent
`~/.agents/skills` directement), par exemple :

```sh
mkdir -p ~/.votremoteur/skills ~/.votremoteur/agents
for d in ~/.agents/skills/*/; do ln -s "$d" ~/.votremoteur/skills/"$(basename "$d")"; done
for a in ~/.agents/agents/*.md; do ln -s "$a" ~/.votremoteur/agents/; done
```

**Hooks** : appeler `dispatch.py` avec l'événement en argument, en
exportant `AGENT_CONFIG_ROOT` vers la racine du harnais. Exemple complet
pour un moteur au format hooks Claude Code (ZCode, autres) :

```json
{
  "hooks": {
    "enabled": true,
    "events": {
      "SessionStart": [
        { "hooks": [{ "type": "command",
          "command": "AGENT_CONFIG_ROOT=/home/moi/.agents python3 -E -s /home/moi/.agents/hooks/dispatch.py SessionStart",
          "timeout": 15 }] }
      ],
      "UserPromptSubmit": [
        { "hooks": [{ "type": "command",
          "command": "AGENT_CONFIG_ROOT=/home/moi/.agents python3 -E -s /home/moi/.agents/hooks/dispatch.py UserPromptSubmit",
          "timeout": 30 }] }
      ],
      "PreToolUse": [
        { "hooks": [{ "type": "command",
          "command": "AGENT_CONFIG_ROOT=/home/moi/.agents python3 -E -s /home/moi/.agents/hooks/dispatch.py PreToolUse",
          "timeout": 10 }] }
      ],
      "PostToolUse": [
        { "matcher": "Write|Edit",
          "hooks": [{ "type": "command",
            "command": "AGENT_CONFIG_ROOT=/home/moi/.agents python3 -E -s /home/moi/.agents/hooks/dispatch.py PostToolUse",
            "timeout": 150 }] }
      ],
      "Stop": [
        { "hooks": [{ "type": "command",
          "command": "AGENT_CONFIG_ROOT=/home/moi/.agents python3 -E -s /home/moi/.agents/hooks/dispatch.py Stop",
          "timeout": 400 }] }
      ]
    }
  }
}
```

Le protocole parlé par `dispatch.py` est celui des hooks Claude Code :
JSON sur l'entrée standard, sortie JSON (`decision`, `permissionDecision`,
`additionalContext`) ou code de sortie (`2` = blocage).

## Ce que ce dépôt ne contient pas, volontairement

`memory/` (faits du poste et des projets), `BRAIN.md` (carte de la
machine), `HISTORIQUE.md` (journal), `docs/justifications/` (un document
par choix technique), `archives/` .

## Licences

Code du harnais : MIT (voir `LICENSE`). Skills importés : voir
`.skill-lock.json` pour leur source d'origine.

# Harnais agentique

Un harnais de travail pour agents de code : règles permanentes, garde-fous
exécutés en hooks, 202 skills, 5 sous-agents en lecture seule, et un
verifier qui contrôle le tout à chaque fin de tour.

## Principes

- **La preuve, pas le récit.** Chaque affirmation s'appuie sur une sortie
  fraîche (`fichier:ligne`), jamais sur le compte rendu d'un agent.
- **Un seul écrivain.** Les sous-agents lisent et rendent un rapport ; le
  fil principal écrit, puis revérifie le rapport avec une preuve neuve.
- **Les règles sont tenues par la machine.** Les gates (Stop, PostToolUse)
  bloquent la fin de tour si un contrôle échoue ; un avis sans contrôle ne
  vaut rien.
- **La mémoire ne contient que des faits.** Les règles vivent dans
  `AGENTS.md` et `regles/`, nulle part ailleurs.

## Structure

```
AGENTS.md            règles permanentes (méthode, git, tests, mémoire)
regles/bas-niveau.md règles additionnelles OS / noyau / pilotes
DESIGN.md            contrat visuel par défaut de toute UI
skills/              202 skills (frontmatter name + description)
agents/              5 sous-agents lecture seule (architecte, auditeur,
                     chercheur, explorateur, relecteur)
hooks/               dispatch.py (entrée unique) + garde + gates
verifier             contrôle la config : liens, budget, scans, lint, tests
tests/               suite pytest du harnais (187 tests)
.skill-lock.json     provenance et empreinte des skills importés
```

## Installation

```sh
git clone <ce dépôt> ~/.agents
~/.agents/verifier --rapide
```

Le harnais se branche sur un moteur (agent de code) par liens, sans copie :

- les **règles** : lier `AGENTS.md` dans les instructions du moteur ;
- les **skills** et les **agents** : liens symboliques (beaucoup de moteurs
  découvrent `~/.agents/skills` directement) ;
- les **hooks** : appeler `dispatch.py` avec l'événement en argument, en
  exportant `AGENT_CONFIG_ROOT` vers la racine du harnais. Exemple pour un
  moteur au format hooks Claude Code (ZCode, autres) :

```json
{
  "hooks": {
    "enabled": true,
    "events": {
      "PreToolUse": [
        { "hooks": [{ "type": "command",
          "command": "AGENT_CONFIG_ROOT=/home/moi/.agents python3 -E -s /home/moi/.agents/hooks/dispatch.py PreToolUse",
          "timeout": 10 }] }
      ]
    }
  }
}
```

Un moteur par copie : ne faites pas écrire deux moteurs sur le même dépôt.

## Vérifier

```sh
./verifier --rapide
./verifier          # complet, avant de clore un chantier
```

Contrôles : structure et liens des skills et agents, budget du listing,
hooks en python isolé (`python3 -E -s`), refus de secrets, gitleaks,
semgrep, ruff, shellcheck, suite pytest. Les contrôles liés au poste
(moteur branché, outillage installé) passent en « non lancés » si le
fichier visé est absent.

## Ce que ce dépôt ne contient pas, volontairement

`memory/`, `BRAIN.md`, `HISTORIQUE.md`, `docs/justifications/`,
`archives/` : données personnelles, état du poste et justifications
internes ne se publient pas. La suite de tests publique est ajustée en
conséquence : les tests qui lisent ces fichiers sont retirés ou sautés si
l'outil visé n'est pas installé.

## Skills

Une partie des 202 skills est importée : `.skill-lock.json` trace la
source GitHub et l'empreinte de chaque dossier importé.

## Licence

MIT — voir `LICENSE`.

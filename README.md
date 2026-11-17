# Harnais agentique

Un harnais de travail pour agents de code : règles permanentes,
garde-fous exécutés en hooks, 202 skills, 5 sous-agents en lecture
seule, et un verifier qui contrôle l'ensemble. Conçu pour qu'un agent
travaille en mode automatisé sans supervision tour par tour : ce qu'il
affirme est prouvé, ce qui est dangereux est intercepté avant
d'exécuter, ce qui est livré est re-vérifié avant de rendre la main.

## Le problème traité

Un agent de code laissé en autonomie échoue de façon répétée et
prévisible :

- il **raconte au lieu de prouver** : « les tests passent » sans sortie
  relue, « corrigé » sans diff vérifié ;
- il **touche des secrets** (« j'ai juste regardé le `.env` ») et peut
  les recopier dans un livrable ;
- il lance des **commandes irréversibles** (`rm -rf`, écriture disque,
  flash firmware, `git reset --hard`) sans comprendre la portée ;
- il **dérive de ses règles** au fil du contexte : les consignes du
  premier tour ne survivent pas à la dixième fichier ;
- à plusieurs agents, il **écrivent en parallèle** sur les mêmes
  fichiers et se corrigent mutuellement en boucle.

Le problème traité : **déléguer du travail réel à un agent, en mode
automatisé (intervention minimale), sans perdre ni les secrets, ni les
données locales, ni l'intégrité du dépôt, ni la vérité des annonces.**
La réponse n'est pas un meilleur prompt : c'est un contrat comportemental
court (AGENTS.md) **renforcé par des contrôles machine** que l'agent ne
peut pas contourner parce qu'ils ne s'exécutent pas en lui.

## Fonctionnement architectural

Une source de vérité, des moteurs branchés dessus :

```
            ┌───────────────── moteur A (ZCode…) ─────────────────┐
            │  instructions ← lien AGENTS.md                      │
            │  skills/agents ← liens symboliques                 │
            │  événements → hooks enregistrés chez le moteur     │
            └──────────────────────────┬──────────────────────────┘
                                       │ AGENT_CONFIG_ROOT=<copie du harnais>
~/.agents (une copie par moteur)       ▼
├── AGENTS.md            règles permanentes — la seule source des règles
├── regles/bas-niveau.md règles OS/noyau : spec matérielle citée,
│                         preuve par paliers (hôte, QEMU, machine)
├── DESIGN.md            contrat visuel par défaut de toute UI
├── skills/              202 skills (frontmatter name+description ≤1024)
├── agents/              5 sous-agents lecture seule (sans shell)
├── hooks/dispatch.py    ENTRÉE UNIQUE de tous les hooks
├── verifier             contrôle la config entière
└── memory/              faits (jamais de règles) — privée, non publiée
```

**Cycle d'un tour.** Le moteur déclenche les hooks ; `dispatch.py`
(traduit au passage les noms d'outils du moteur hôte) route :

| Événement | Contrôle | Effet |
|---|---|---|
| `PreToolUse` | garde : secrets (chemins bruts **et résolus**, catalogue étendu), `rm` récursif, écriture disque/firmware, force-push, marqueurs de désactivation, verrou d'écrivain du dépôt | `deny` ou `ask` **avant** l'exécution |
| `PostToolUse` (écritures) | shellcheck, checkbashisms, shfmt/ruff, scan cyber | signalé au tour ; les échecs de qualité **tiennent le Stop** jusqu'à correction |
| `Stop` | scan cyber, gitleaks et semgrep sur les projets modifiés, tests de régression, oracle, verifier de config, état du harnais (dégradation, marque d'interruption, verrous) | la main ne revient pas tant qu'un contrôle échoue |
| `SessionStart` / `UserPromptSubmit` | état de session, relecture de l'enregistrement moteur, déclencheurs ponctuels | nettoyage, aiguillage, alerte de dégradation |

**Sous-agents.** Les 5 agents (`architecte`, `auditeur-securite`,
`chercheur`, `explorateur`, `relecteur`) sont lecture seule **technique** :
sans shell (Read, Grep, Glob — web pour le chercheur), liste d'outils
imposée par le moteur et vérifiée par le verifier. Ils rendent un
rapport (≤ 2 000 tokens) que le fil principal revérifie avec une preuve
neuve. Un seul écrivain par dépôt, jamais deux.

**Un moteur par copie, un écrivain par dépôt.** Chaque moteur tient sa
copie du harnais (clonée via git) et exporte `AGENT_CONFIG_ROOT` vers sa
racine ; les copies se synchronisent par le dépôt git amont. Un verrou
d'écrivain par dépôt (session, expiration 6 h, reprise des verrous
morts, rafraîchis à chaque tour du propriétaire) refuse l'écriture
d'une session sur un dépôt déjà tenu par une autre. Deux moteurs sur une même copie = deux écrivains = interdit (et
détecté).

**Budget de contexte.** Le listing des skills est mesuré par le
verifier (33 318 caractères pour 202 skills, plafond 230 000) : la
découverte ne peut pas silencieusement déborder le contexte.

**Pile de skills.** Bas niveau (C, OS, assembleur, noyau, libc, shell
maison), réseau, Android, WordPress, CI/CD, GCP, Postgres, finance
quantitative (pricing, dérivés, risque, ML de marché avec garde-fous
anti-fuite), outillage transverse (TDD, revue minutieuse, audit).
Chaque skill importé est tracé dans `.skill-lock.json` (source,
empreinte).

## Limites du système

Énoncées franchement :

- **Fail-open à l'appel, fail-closed au tour.** La garantie tient à
  l'exécution du hook ; deux cas se distinguent. La *dérive
  d'enregistrement* (hook désactivé, commande modifiée, délai
  raccourci, événement retiré) est rattrapée deux fois : par le
  verifier, qui contrôle l'enregistrement exact de chaque événement,
  et par `dispatch.py`, qui relit l'enregistrement du moteur à chaque
  tour et tient le `Stop` tant qu'un événement attendu manque. Un hook
  tué *à l'exécution* — dépassement de délai (garde 10 s, Stop 400 s),
  crash, événement jamais déclenché — ne peut pas empêcher l'appel qui
  l'a déclenché (après expiration, c'est le moteur, pas le harnais,
  qui décide d'exécuter l'outil) : le garde pose une marque avant son
  verdict et la lève après ; la marque survit au hook tué et le `Stop`
  du tour bloque jusqu'à reprise de l'action sous contrôle. Restent
  hors de portée : l'appel déjà exécuté, et la désactivation totale
  (aucun hook actif — seul un passage du verifier la relève). Un
  moteur sans mécanisme de hooks n'est pas protégé du tout.
- **Une couche, pas deux.** Côté moteurs qui exposent une liste de
  permissions (refus statiques), le garde s'y ajoute et le refus tient
  même hook tué. Côté moteurs qui ne l'exposent pas, le garde est
  l'unique couche — en faire une condition d'installation contrôlée
  par le verifier reste un chantier ouvert.
- **Le plan de contrôle se protège, sans en être hors de portée.** Les
  marqueurs de désactivation (`disable-*`) ne peuvent plus être créés,
  modifiés ni supprimés par l'agent (refus du garde, y compris par
  redirection shell) ; le verifier liste ceux qui existent et l'auteur
  les pose à la main. Le reste du harnais reste accessible en écriture
  à l'agent — c'est voulu, il maintient sa config sur demande — : la
  séparation complète du contrôleur et du contrôlé demanderait un
  compte dédié (chantier ouvert).
- **La lecture seule des sous-agents est technique, pas déclarative.**
  Les 5 agents n'ont plus de shell : Read, Grep, Glob (web pour le
  chercheur), liste imposée par le moteur ; le verifier refuse Bash
  dans un agent. Ce que les agents perdent (git log, find), le brief
  du fil appelant doit le fournir.
- **Les suites de test exécutent du code de projet sous le compte de
  l'utilisateur.** Leur environnement est épuré (plus de variables
  secrètes ni de sockets d'agents d'authentification) et leur réseau
  externe est coupé par bwrap (`--unshare-net`, loopback debout : les
  tests d'intégration locaux passent, bwrap absent = avertissement
  explicite). Restent : pas de compte dédié, accès disque complet.
- **Le Stop ne couvre que le lanceur reconnu.** Un projet sans suite de
  tests reconnue n'a pas de gate de régressions ; l'oracle ne mord que
  si le projet en fournit un.
- **Gates typées par langage.** Format et lint ciblent shell et Python
  (shfmt, shellcheck, checkbashisms, ruff) ; le C dépend des règles du
  projet (`-Wall -Wextra -Werror`) ; les secrets du projet passent par
  gitleaks au Stop et le code web/python par semgrep (alertes ERROR,
  règles python + OWASP top dix) ; les autres langages n'ont pas de
  SAST dédié.
- **Le push normal est contractuel.** Force-push est confirmé par le
  garde ; un push ordinaire n'est pas intercepté mécaniquement — il
  repose sur la règle « jamais de push sans demande ».
- **La qualité du raisonnement reste hors de portée machine.** Le
  harnais contraint les actions et vérifie les artefacts ; il ne prouve
  pas la pertinence d'une conception. La preuve fraîche est un contrat
  comportemental pour tout ce qui n'est pas mécaniquement contrôlable.
- **Coût.** ~2 min de verifier quand la config change (Stop), ~50 Ko de
  règles chargées à chaque session, un contrôle PreToolUse sur chaque
  appel d'outil.
- **Dérive entre copies.** Un moteur par copie protège l'écriture
  simultanée, renforcée par un verrou d'écrivain par dépôt (refus
  d'écrire sur un dépôt déjà tenu par une autre session, expiration
  6 h) ; les copies divergent si on ne synchronise pas par git.
- **Périmètre moteur.** Le vocabulaire d'événements, les matchers
  (regex) et les délais dépendent du moteur ; l'adaptation est écrite
  dans la copie, pas dans le harnais commun.

**Chantiers ouverts** (assumés, non implémentés) : compte dédié et
permissions filesystem pour les suites de test (le réseau est déjà
coupé), permissions natives du moteur comme condition d'installation,
provenance amont des skills par commit (le lock vérifie déjà
l'empreinte locale de chaque skill importé), ouverture de fichiers sans
suivi des liens côté moteur.

## Modèle de menace

**Actifs à protéger.** Secrets locaux (`.env`, clés SSH, credentials),
intégrité du poste (disques, firmware, données hors dépôt), travail
local non commité, confidentialité de la mémoire du harnais (faits du
poste et des projets), vérité des livrables (annonces de tests,
contenu publié).

**Adversaire.** L'agent lui-même — par inadvertance, par injection de
contenu (un fichier lu qui contient des instructions), ou par deux
instances concurrentes. **Pas** un attaquant qui contrôle la machine ou
le moteur : contre lui, le harnais n'offre rien (voir hors modèle).

| Risque | Interception | Ce qui reste non couvert |
|---|---|---|
| Lecture/exfiltration d'un secret | garde `deny` : chemins bruts **et résolus** (liens symboliques), motifs d'interpréteur (`python -c open(".env")`…), catalogue étendu (kube, docker, gcloud, npmrc, pypirc, `.pem` privées) ; gitleaks sur ce qui est écrit | un secret déjà recopié hors motifs ; l'appel exécuté avant un hook tué (la marque d'interruption tient le tour) |
| Commande irréversible (`rm -rf`, `dd`, firmware) | garde `ask`/`deny` avant exécution | rien, si le hook tourne |
| Perte de travail local (`git clean`, `reset --hard`) | garde de dépôt : travail non commité détecté | commits déjà poussés de force (confirmé seulement) |
| Désactivation silencieuse d'un contrôle | marqueurs `disable-*` refusés au garde (création, modification, suppression, redirections) et listés par le verifier ; événement retiré du moteur détecté à chaque tour, `Stop` tenu | désactivation totale : aucun hook ne peut s'exécuter pour le constater |
| Sous-agent qui écrit malgré « lecture seule » | plus de shell dans les agents (liste d'outils imposée par le moteur) ; le verifier refuse Bash dans un agent | le fil appelant reste écrivain unique, ses propres appels shell restent du ressort du garde |
| Code de projet exécuté par l'automatisation (suites de test) | environnement épuré (variables secrètes masquées, sockets d'authentification retirées), réseau externe coupé (bwrap) | accès disque complet du compte utilisateur, pas de compte dédié |
| Secret dans le livrable | gitleaks + semgrep sur le harnais (PostToolUse et Stop) ; gitleaks + semgrep (ERROR, web/python) sur les projets modifiés au Stop | faux négatifs des scanners, SAST limité aux langages couverts |
| Tests verts annoncés sans preuve | gate Stop relance la suite ; tests sans assertion bloquants ; oracle teste une implémentation fausse ; shellcheck/format tiennent le Stop jusqu'à correction | suites non reconnues par le lanceur |
| Injection par contenu lu | sous-agents sans shell, revérification par le fil, secrets refusés même « demandés » | instruction bénigne exécutée sans déclencheur (aucune sandbox) |
| Deux moteurs ou sessions sur un dépôt | un moteur par copie + `AGENT_CONFIG_ROOT` ; verrou d'écrivain par dépôt (refus avant écriture, expiration 6 h) ; divergence détectée par le verifier | écritures par shell brut (le verrou protège les outils d'écriture) ; désynchronisation sans git pull |

**Hors du modèle** : compromission du moteur ou de l'OS, exfiltration
réseau par un processus non passé par les hooks, attaques physiques,
canaux latéraux. Le harnais est un contrôle d'actions de l'agent, pas
un confinement — il n'y a pas de sandbox.

## Prérequis

- Linux (écrit et éprouvé sur Ubuntu), `bash`, `git`.
- Python ≥ 3.11 (`tomllib`), avec `pytest`.
- Outils des contrôles : `jq`, `ruff`, `shellcheck`, `checkbashisms`
  (paquet devscripts), `shfmt`, `gitleaks`, `semgrep`. Un outil absent
  est signalé (« ne pas annoncer de validation ») — le verifier ne
  ment jamais sur ce qu'il n'a pas lancé. Au premier passage, semgrep
  télécharge ses règles (réseau), puis les garde en cache.
- `bwrap` (bubblewrap), recommandé : coupe le réseau externe des suites
  de test tout en laissant le système de fichiers et le loopback
  intacts. Absent, le lanceur prévient et continue sans isolation.
- Un moteur à hooks (protocole Claude Code : ZCode, Claude Code, Grok)
  pour la partie dynamique. Les règles, skills et agents s'utilisent
  sans moteur.
- ~30 Mo.

## Installation

```sh
git clone <ce dépôt> ~/.agents
~/.agents/verifier --rapide        # doit finir vert avant de continuer
```

Brancher votre moteur — **un moteur par copie**, jamais deux écrivains
sur le même dépôt :

**Règles** : lier `AGENTS.md` dans les instructions du moteur.

**Skills et agents** : liens symboliques (beaucoup de moteurs
découvrent `~/.agents/skills` directement) :

```sh
mkdir -p ~/.votremoteur/skills ~/.votremoteur/agents
for d in ~/.agents/skills/*/; do ln -s "$d" ~/.votremoteur/skills/"$(basename "$d")"; done
for a in ~/.agents/agents/*.md; do ln -s "$a" ~/.votremoteur/agents/; done
```

**Hooks** : enregistrer `dispatch.py` sur les événements, en exportant
`AGENT_CONFIG_ROOT` vers la racine du harnais. Exemple complet pour un
moteur au format Claude Code :

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
        { "matcher": "Write|Edit|MultiEdit|NotebookEdit|ApplyPatch",
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

Le protocole parlé par `dispatch.py` : JSON sur l'entrée standard,
sortie JSON (`decision`, `permissionDecision`, `additionalContext`) ou
code de sortie (`2` = blocage).

**Contenu volontairement absent** de ce dépôt : `memory/`, `BRAIN.md`,
`HISTORIQUE.md`, `docs/justifications/`, `archives/` — données
personnelles, état du poste et justifications internes ne se publient
pas. La suite de tests publique est ajustée en conséquence (tests
retirés ou sautés si l'outil visé est absent).

## Validation

Trois étages, tous rejouables :

```sh
# 1. La suite du harnais (189 tests) : structure, garde, gates, verifier.
python3 -m pytest tests/

# 1 bis. La suite des hooks (110 tests) : garde, gates, fail-closed,
# verrou d'écrivain, marqueurs, liens symboliques, environnement épuré.
python3 -m pytest hooks/verify.py

# 2. Le verifier complet.
./verifier                 # ou --rapide (~40 s)

# 3. Bout en bout, sur payloads réels :
echo '{"tool_name":"Read","tool_input":{"file_path":"'"$HOME"'/.ssh/id_rsa"},"cwd":"'"$HOME"'"}' \
  | AGENT_CONFIG_ROOT="$HOME/.agents" python3 -E -s ~/.agents/hooks/dispatch.py PreToolUse
# attendu : {"permissionDecision":"deny", ...}

echo '{"session_id":"essai","stop_hook_active":false}' \
  | AGENT_CONFIG_ROOT="$HOME/.agents" python3 -E -s ~/.agents/hooks/dispatch.py Stop
# attendu : sortie JSON vide, code 0
```

Le verifier contrôle : frontmatter et liens des skills et agents,
budget du listing, hooks en python isolé (`python3 -E -s`, délais
exacts), refus de secrets, gitleaks, semgrep, ruff, shellcheck,
checkbashisms, suite pytest. Les contrôles liés au poste passent en
« non lancés » si le fichier visé est absent — le dépôt est vert sur
toute machine, sans mentir sur ce qui n'a pas tourné.

Un détail de conception : la gate oracle teste volontairement une
**implémentation fausse** (`hooks/oracle_vide.py`) pour prouver que les
tests mordent — un test qui ne distingue pas le vrai du faux ne vaut
rien.

# 4. Installation vierge, rejouable :
git clone <ce dépôt> harnais-neuf
cd harnais-neuf && mkdir home-isole && HOME="$PWD/home-isole" ./verifier --rapide
# attendu : 0 KO ; les contrôles liés au moteur passent en « non lancés ».
# Sur la machine de l'auteur, si le moteur vivant est câblé sur une autre
# copie du harnais, ces mêmes contrôles passent KO : le verifier compare
# l'enregistrement du moteur à SA racine, il ne mente pas sur ce qu'il voit.

## Résultats expérimentaux

Observations d'usage réel, pas un benchmark contrôlé.

**Terrain.** Un mois d'usage quotidien en développement personnel :
248 sessions réparties sur 33 projets. 202 skills actifs, listing
mesuré à 33 318 caractères — 15 % du plafond de 230 000, contrôlé à
chaque passage du verifier.

**Ce qui se passe en développement, tour après tour.**

- **Garde `PreToolUse` sur chaque appel d'outil** : réponse < 1 s pour
  un budget de 10 s. En pratique il laisse passer le travail courant
  sans friction et intercepte ce qui sort du cadre : lecture d'une
  clé SSH refusée (`permissionDecision: deny`), confirmation exigée
  avant `rm` récursif, écriture disque ou force-push.
- **Gates d'écriture (`PostToolUse`)** : chaque script shell modifié
  passe shellcheck et checkbashisms (< 1 s), chaque fichier formaté ;
  un avertissement shellcheck tient le tour jusqu'à correction.
- **Stop** : la suite de régressions du projet est relancée à chaque
  fin de tour sur les fichiers touchés ; une régression KO bloque le
  rendu de la main. Quand la config du harnais a changé pendant le
  tour, le verifier `--rapide` s'ajoute (~2 min).
- **Ce que ça coûte** : ~40 s de verifier occasionnellement au Stop,
  moins d'une seconde par appel d'outil, 33 318 caractères de listing
  dans le contexte.

**Mesures des contrôles** (dépôt complet, machine de dev) :

| Contrôle | Durée |
|---|---|
| Suite des hooks (`verify.py`, 110 cas) | ~104 s |
| Tests du verifier (194 cas privés, 189 publics) | ~2 s |
| gitleaks | 0,9 s |
| semgrep (harnais) / SAST projet au Stop | 3,5 s / ~2 s |
| ruff, shellcheck, checkbashisms | < 1 s chacun |
| Verifier `--rapide` complet | ~112 s |

**Ce que ces nombres ne disent pas.** La couverture des gates de
régressions dépend du lanceur reconnu dans chaque projet ; la part
comportementale (preuve fraîche, revérification des rapports) est un
contrat, dont on observe qu'il tient tant que les règles restent
chargées et courtes — c'est précisément ce que le verifier budgete.

## Licence

Code du harnais : MIT (voir `LICENSE`). Skills importés : voir
`.skill-lock.json` pour leur source d'origine.

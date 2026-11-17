---
name: norme-cybersecurite
description: >-
  Contrôle la baseline sécu et corrige les hits avant livraison. Use when code touches input, HTML, SQL, shell, files, auth or secrets, or when the cyber scan flags a line.
---

# Norme cybersécurité

## Invariant

**PERMANENT jusqu'à nouvel ordre explicite de l'auteur.**

Check, puis correctif dans le même tour. Une livraison n'est valide que si le scan sécu de ce tour sort 0.

Violer la lettre, c'est violer l'esprit.

## Baseline (tout projet)

Interdit dans le code livré :

- `innerHTML`, `dangerouslySetInnerHTML`, `document.write`, `v-html`, `eval`, `new Function`
- SQL ou shell construit avec l'entrée utilisateur
- `strcpy`, `strcat`, `gets`, `sprintf`, `scanf("%s")` sur une entrée
- chemin utilisateur sans rejet de `..`
- objet lu ou modifié avec un id qui n'appartient pas à l'utilisateur
- secret, jeton, clé privée, mot de passe dans le dépôt, la mémoire ou un log

Scan :

```bash
~/.agents/hooks/cyber-scan.sh <fichier-ou-dossier>
```

Sortie vide et exit 0 : baseline OK. Une ligne : corriger le code, relancer, lire la nouvelle sortie.

## Au-delà de la baseline (tout projet)

- Contrôle OWASP du flux touché, dans le même tour : validation des entrées, contrôle d'accès, erreurs sans fuite d'information.
- Auth, paiement ou données personnelles : audit OWASP complet du flux et hardening (sessions, cookies, en-têtes, limitation de débit).
- CSP, SRI, 2FA ou captcha seulement si le brief ou le flux le demande.

## Désactivation

Uniquement si l'auteur dit « arrête la cyber », « plus de check sécu », « excepte ce projet de la cyber », ou si le fichier `~/.agents/hooks/disable-norme-cybersecurite` existe.

## Rationalisations à rejeter

| Excuse | Réalité |
|--------|---------|
| « C'est un devoir, la sécu attend » | La baseline et l'OWASP du flux touché tiennent partout |
| « Le scan est un faux positif, je livre » | Corriger, ou l'ajouter à `.cyber-ignore` (racine du projet) en disant pourquoi la ligne est sûre |
| « J'ajoute un captcha pour être propre » | Hors brief, on n'ajoute pas |
| « Le scan d'hier était vert » | Relancer sur le code de ce tour |

## Drapeaux rouges. STOP

- Livrer avec un hit de `cyber-scan.sh`
- Coller un jeton du chat dans un fichier ou la mémoire
- Annoncer « sécu OK » sans sortie du scan

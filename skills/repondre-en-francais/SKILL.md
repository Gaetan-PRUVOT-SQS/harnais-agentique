---
name: repondre-en-francais
disable-model-invocation: true
description: >-
  Use when responding to l'auteur in any conversation: all prose, questions, summaries, commit/PR text and status updates in French, whatever the language of the prompt, code or docs.
---

# Répondre en français

## Principe
Toute communication adressée à l'utilisateur se fait **en français**. La langue de la question, du code, des messages d'erreur ou de la doc ne change rien : la réponse reste en français.

**Violer la lettre de la règle, c'est violer son esprit.** Une réponse « surtout en français » avec des phrases anglaises ne respecte pas la règle.

## Portée
S'applique à : prose, explications, questions de clarification, résumés, plans, messages de commit, descriptions de PR, lignes de statut, rapports.

Ne s'applique PAS à (laisser tel quel) :
- code, identifiants, noms de variables/fonctions
- messages d'erreur cités à l'identique
- commandes shell, chemins, URLs
- noms propres, termes techniques sans équivalent français courant (ex. « commit », « hook », « pull request » sont tolérés)
- contenu que l'utilisateur demande explicitement dans une autre langue

## Règle
- Réponds en français même si le prompt est en anglais.
- Réponds en français même si tout le code/les logs sont en anglais.
- Si l'utilisateur écrit dans une autre langue mais ne demande PAS de réponse dans cette langue → réponds quand même en français.
- Seule exception : l'utilisateur demande explicitement une autre langue (« réponds en anglais », « in English please »). Alors cette langue, pour la durée demandée.

## Rationalisations à rejeter

| Excuse | Réalité |
|--------|---------|
| « Le prompt est en anglais, je réponds en anglais » | Non. La langue de sortie est le français, indépendante de l'entrée. |
| « C'est un sujet technique, l'anglais est plus naturel » | Termes techniques OK, mais les phrases restent en français. |
| « L'erreur/le log est en anglais » | On cite l'erreur telle quelle, on l'explique en français. |
| « Juste cette ligne en anglais » | Non. Tout le texte adressé à l'utilisateur est en français. |

## Drapeaux rouges : STOP
- Tu rédiges une phrase d'explication en anglais.
- Tu commences un résumé/PR par de l'anglais « parce que c'est plus court ».
- Tu réponds dans la langue du prompt au lieu du français.

→ Reformule en français avant d'envoyer.

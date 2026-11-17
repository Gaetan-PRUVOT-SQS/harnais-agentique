---
name: crm
description: 'Use to design, build, review or test a CRM (accounts, contacts, leads, pipeline, import, integrations): data model, multi-tenant permissions, API, GDPR/CNIL, performance, test journeys.'
---
# CRM : conception, réalisation, revue et tests

Un CRM contient surtout des données personnelles de tiers. La sécurité ne se négocie pas et aucun échec de test n'est toléré :
pas de quarantaine pour passer au vert, pas de test qui ne passe qu'en le relançant. Ce skill ne répète pas les skills
généraux, il y renvoie : `general-engineering`, `security-gate`, `react-spa`, `android-dev`, `qa-e2e`,
`feature-test-pipeline`, `validation-gate`, `devops-ci`.

## 1. Avant de coder

- [ ] Écrire en une page le processus commercial réel : qui crée un lead, qui le qualifie, quand il devient opportunité, qui signe. Un CRM qui impose un processus imaginaire ne sera pas utilisé.
- [ ] Lister les rôles réels (commercial, manager, marketing, support, admin tenant, admin plateforme) et ce que chacun doit voir et modifier.
- [ ] Choisir le modèle d'isolation (section 6.1) avant le premier schéma.
- [ ] Modèle de menace STRIDE et LINDDUN, et exigences ASVS retenues (voir `security-gate` 3.1).
- [ ] Registre des traitements, base légale par finalité, durées de conservation écrites (section 9).
- [ ] Mesurer ce que coûte la saisie : chaque champ obligatoire doit se justifier. La saisie trop longue est la première raison pour laquelle les commerciaux évitent l'outil.

## 2. Modèle de données

### 2.1 Entités cœur

| Entité | Rôle | Points d'attention |
|---|---|---|
| Tenant (organisation, workspace) | frontière d'isolation | présent sur chaque ligne métier, ou schéma dédié |
| Utilisateur, équipe, unité | propriété et droits | un utilisateur peut être dans plusieurs équipes |
| Compte (société) | entité B2B | domaine web normalisé, utile au dédoublonnage |
| Contact (personne) | personne physique | données personnelles, consentements, opposition |
| Lead | prospect pas encore qualifié | se convertit en contact, compte et opportunité |
| Opportunité (deal) | vente en cours | montant, devise, étape, date de clôture prévue, motif de perte |
| Pipeline et étape | processus de vente | plusieurs pipelines par tenant, étapes ordonnées, probabilité et catégorie de prévision par étape |
| Activité | e-mail, appel, réunion, note, tâche | rattachée à plusieurs fiches (contact, compte, opportunité) |
| Produit, liste de prix, devis, ligne de devis | chiffrage | montants en entier (centimes) ou décimal exact, jamais en flottant |
| Consentement et opposition | preuve RGPD | canal, finalité, date, source, texte présenté (version) |
| Journal d'audit | qui a fait quoi | ajout seul, séparé des tables métier |

### 2.2 Règles de modèle

- Identifiants : UUID (v7 si l'ordre d'insertion compte pour les index). Ils sont opaques, mais ce n'est pas une autorisation.
- Chaque fiche porte `tenant_id`, `owner_id`, `created_by`, `created_at`, `updated_by`, `updated_at`, `version` (pour la concurrence optimiste), et `deleted_at` si la corbeille existe.
- Relations : maître-détail (l'enfant suit le parent, suppression en cascade) ou simple référence (la référence passe à null). Ce choix est explicite pour chaque lien.
- Activités : table polymorphe avec une table de liaison (activité vers N fiches), pas une colonne par type de parent.
- Montants : devise sur la fiche, taux de conversion daté et stocké, total recalculé côté serveur.
- E-mail en minuscule normalisée, téléphone en E.164, domaine de société sans `www`. Ces formes normalisées servent au dédoublonnage.
- Dates et heures en UTC en base, fuseau de l'utilisateur à l'affichage.

### 2.3 Champs et objets personnalisés

Les champs sont décrits par des métadonnées (objet, champ, type, obligatoire, règles de validation, index, droits),
comme le font Salesforce et Twenty. Le choix du stockage :

| Option | Pour | Contre | Quand |
|---|---|---|---|
| Colonnes typées | types, contraintes et index natifs | migration à chaque champ | champs standard du produit |
| JSONB par fiche | pas de migration, une ligne par fiche | validation dans l'application, pas de clé étrangère | champs personnalisés, choix par défaut |
| EAV, une table par type | intégrité en base | une jointure par filtre, rapports pénibles | peu de champs, forte exigence d'intégrité |
| Schéma par tenant avec DDL | colonnes réelles | migrations multipliées par le nombre de tenants | peu de tenants, gros volumes chacun |

- [ ] Valeurs JSONB validées côté serveur avec le schéma généré depuis les métadonnées, à chaque écriture (API, import, automatisation).
- [ ] Champ filtrable ou triable : index d'expression, B-tree sur la valeur castée pour les nombres (`((custom->>'montant')::numeric)`). Pour les dates, stockage ISO 8601 et index sur le texte, car le cast texte vers date n'est pas IMMUTABLE.
- [ ] Nombre de champs personnalisés plafonné par objet et par tenant.
- [ ] Suppression d'un champ : corbeille d'abord, purge ensuite, et contrôle des usages (vues, rapports, automatisations) avant.
- [ ] Les noms de champs fournis par un tenant ne sont jamais concaténés dans du SQL : passage par une table de correspondance et des identifiants contrôlés.

### 2.4 Historique, corbeille, effacement

- Historique par champ (ancienne valeur, nouvelle valeur, auteur, date, source : interface, API, import, automatisation) pour les champs qui comptent : étape, montant, propriétaire, consentements.
- Corbeille avec délai court (Salesforce garde 15 jours), restauration qui recâble les enfants et les références.
- L'effacement RGPD est une vraie suppression, et la corbeille ne suffit pas. Il couvre la base, l'index de recherche, les caches, les fichiers, les exports générés et les copies chez les sous-traitants. Pour les sauvegardes, on documente le délai d'expiration et on rejoue la liste des effacements après toute restauration.
- L'historique et l'audit d'une personne effacée sont pseudonymisés, pas gardés en clair.

## 3. Fonctionnalités par priorité

### MVP (sans ça, ce n'est pas un CRM utilisable)
- Comptes, contacts, leads, opportunités, avec fiche, liste filtrable et recherche globale.
- Pipeline en kanban et en liste, changement d'étape par glisser-déposer et au clavier.
- Activités et timeline unifiée sur chaque fiche (notes, tâches, appels, réunions, e-mails).
- Tâches avec échéance et rappels, vue « mes tâches du jour ».
- Conversion lead vers contact, compte et opportunité, avec contrôle de doublons.
- Propriété des fiches, réattribution, rôles et équipes (section 6).
- Import CSV avec correspondance de colonnes, aperçu, rapport ligne par ligne. Export CSV protégé (section 5).
- Détection de doublons à la création, à l'import et via l'API.
- Consentements et opposition par canal, liste d'opposition.
- Journal d'audit, historique des champs clés.
- Tableaux de bord simples : pipeline par étape, prévision pondérée, activités par commercial.

### V2
- Synchro e-mail et agenda (Gmail, Microsoft 365) avec rattachement automatique aux fiches.
- Champs personnalisés, puis objets personnalisés.
- Automatisations déclenchées par un événement (création, changement d'étape, date) : créer une tâche, notifier, mettre à jour un champ.
- Scoring de lead par règles explicables (points par propriété et par événement, plafonds, seuils MQL et SQL).
- Devis et produits, listes de prix, PDF.
- Webhooks sortants et API publique documentée (OpenAPI).
- Fusion de doublons avec choix champ par champ.
- Application mobile, consultation hors ligne puis saisie hors ligne.

### Plus tard, après décision explicite
- Prévisions collaboratives avec ajustement des managers.
- Territoires, unités hiérarchiques.
- Scoring prédictif : seulement s'il explique ses facteurs, après une AIPD.
- Enrichissement par sources tierces : hors référentiel CNIL, il faut informer chaque personne sous un mois et faire une AIPD.

### Ce qui fait adopter un CRM
- Capture automatique : e-mails, réunions et appels journalisés sans ressaisie.
- Peu de champs obligatoires, ajoutés au moment où ils servent (le motif de perte à la clôture, pas à la création).
- Édition en ligne, raccourcis clavier, création rapide depuis n'importe où.
- Vues enregistrées par utilisateur, filtres dans l'URL (voir `react-spa`).
- Données de démonstration et parcours guidé à la première connexion, import en premier écran.

## 4. Cycle de vie, pipeline et prévisions

- Séparer **l'étape de cycle de vie** (abonné, lead, MQL, SQL, opportunité, client) et **le statut du lead** (nouveau, tentative de contact, joint, non qualifié, mauvais moment).
- Les automatismes ne font qu'avancer l'étape. Revenir en arrière est une action manuelle, tracée.
- Dates d'entrée et de sortie de chaque étape, temps cumulé par étape : ça sert à la vélocité et aux relances (« SQL depuis plus de 5 jours sans activité »).
- Chaque étape d'opportunité a des critères d'entrée et de sortie écrits, une probabilité par défaut et une catégorie de prévision (pipeline, meilleur cas, engagé, clos).
- Prévision pondérée = somme de montant x probabilité, calculée par période sur la date de clôture prévue. Gagné et perdu sont des états finaux, avec un motif de perte obligatoire.
- Une opportunité gagnée ne se modifie plus sans droit spécifique, et la modification est auditée.

## 5. Doublons, import, export

### Doublons
- Règle de correspondance (ce qui est un doublon : e-mail normalisé, domaine plus nom, téléphone E.164, nom plus société) séparée de la règle d'action (bloquer, alerter, signaler).
- Clés de correspondance indexées pour ne comparer que les candidats plausibles.
- Le contrôle ne révèle jamais une fiche que l'utilisateur ne peut pas voir. S'il en trouve une, le message reste neutre (« doublon possible, voir avec un administrateur ») et ne donne ni nom ni identifiant.
- Fusion : droit réservé, choix de la fiche maîtresse, valeurs choisies champ par champ, enfants rattachés, consentement le plus restrictif conservé, opposition jamais perdue, audit de la fusion, annulation possible pendant un délai.
- Doublons voulus (fournisseur et client) marqués comme tels, jamais refusionnés automatiquement.

### Import
- [ ] Traitement en tâche de fond, avec quota par tenant, progression visible et reprise possible.
- [ ] Encodage détecté (UTF-8 avec ou sans BOM, Windows-1252), séparateur `,` ou `;` (Excel en français), guillemets, retours à la ligne dans un champ.
- [ ] Taille maximale et nombre de lignes plafonnés, type MIME et extension vérifiés.
- [ ] Mode simulation d'abord, puis rapport par ligne (créée, mise à jour, ignorée, erreur et raison).
- [ ] Dédoublonnage dans le fichier et contre la base, avec une clé d'upsert choisie explicitement.
- [ ] Liste d'opposition appliquée : une personne opposée n'est pas réimportée comme contactable.
- [ ] Source et date d'import enregistrées. Si les données viennent d'un tiers, l'information de la personne est prévue sous un mois.
- [ ] Mêmes validations et mêmes droits que l'API, sans aucun raccourci.

### Export
- [ ] Droit d'export distinct du droit de lecture, et limité aux champs que l'utilisateur peut lire.
- [ ] Neutralisation des formules : toute cellule qui commence par `=`, `+`, `-`, `@`, tabulation, CR, LF ou leur variante pleine chasse est préfixée, chaque champ est entre guillemets, les guillemets internes sont doublés. Excel peut retirer ces protections après enregistrement puis réouverture, donc l'export « tableur » et l'export « machine » sont deux formats séparés.
- [ ] Gros export en tâche de fond, fichier dans un stockage par tenant, lien signé à usage court, expiration et purge.
- [ ] Chaque export est audité (qui, quand, quel filtre, combien de lignes).

## 6. Permissions et multi-tenant

### 6.1 Isolation
- Le contexte tenant vient de l'identité vérifiée côté serveur et d'une appartenance active. Un tenant passé par le client (en-tête, paramètre) ne sert qu'à choisir, jamais à prouver.
- Tables partagées avec RLS PostgreSQL :
  - `ENABLE` et `FORCE ROW LEVEL SECURITY` sur chaque table métier ;
  - rôle applicatif sans `SUPERUSER` ni `BYPASSRLS`, vérifié dans `pg_roles` sur l'environnement déployé ;
  - contexte posé dans la transaction par `set_config('app.current_tenant', $1, true)`, lu par `current_setting` sans `missing_ok` pour échouer fermé ; jamais de `SET` de session avec un pool.
- Le dépôt applicatif filtre aussi par tenant (défense en profondeur). Une ressource d'un autre tenant renvoie 404.
- Clés de cache, de file, d'idempotence, de stockage et d'index de recherche préfixées par le tenant.
- Le consommateur d'une file rétablit le contexte et revérifie les droits, car le message seul ne prouve rien.
- Les accès d'administration plateforme passent par un chemin séparé, autorisé à part et audité.
- Restauration d'un seul tenant : dans une base à part, puis recopie ciblée, jamais d'écrasement de la base vive.
- RLS sur tables partagées ou schéma par tenant : le choix dépend du nombre de tenants visé et du volume de chacun. Il se prend explicitement avec le propriétaire du projet avant le premier schéma.

### 6.2 Modèle de droits
- Rôles qui portent des privilèges par objet : créer, lire, modifier, supprimer, attribuer, partager, exporter, fusionner.
- Portée de chaque privilège : mes fiches, mon équipe, mon unité et ses sous-unités, tout le tenant.
- Propriété par utilisateur ou par équipe. Le partage fiche par fiche est réservé aux exceptions, car il coûte cher et se dépanne mal.
- Droits par champ (lecture, écriture) pour les champs sensibles : montant, marge, notes RH, données de santé si jamais il y en a. Un droit de champ ne donne jamais accès à la fiche.
- Règles qui dépendent de l'état : une opportunité gagnée n'est modifiable que par un rôle désigné.
- Changement de droits appliqué tout de suite (sessions et caches de permissions invalidés).
- Unités et équipes calquées sur les besoins d'accès, pas sur l'organigramme, et en petit nombre.
- Pas plus de 10 000 fiches d'un objet sous un même propriétaire ou un même parent. Les leads non attribués vont dans une file, pas chez un utilisateur fictif.
- Toutes les règles sont écrites dans un document de politique (fonction, donnée, champ), et c'est lui qui sert à générer la matrice de tests (section 12).

## 7. API, webhooks, intégrations

### API
- [ ] Autorisation à chaque appel, sur l'objet et sur chaque champ lu ou écrit (BOLA, BOPLA, BFLA).
- [ ] DTO d'entrée par opération avec liste blanche de champs. `tenant_id`, `owner_id`, `version`, les champs calculés et les champs d'audit ne sont jamais acceptés depuis le corps.
- [ ] Sortie filtrée par les droits de champ, pas de sérialisation de l'entité complète.
- [ ] Pagination prévue dès la v1 :
  - jeton de page opaque, chiffré ou signé, qui ne donne aucun droit ;
  - taille par défaut documentée et plafond appliqué ; taille négative = 400 ;
  - pagination par curseur (keyset) sur les grosses listes, jamais d'`OFFSET` profond.
- [ ] Filtres et tris sur une liste blanche de champs indexés.
- [ ] `Idempotency-Key` sur les POST de création. Réponse rejouée à l'identique, erreur si les paramètres diffèrent, clé scopée par tenant, conservée au moins 24 h, sans donnée personnelle dedans.
- [ ] Concurrence optimiste : `ETag` ou `version`, `If-Match` sur les modifications, 412 ou 409 en cas de conflit.
- [ ] Erreurs en `application/problem+json` (RFC 9457), avec `errors[]` et `pointer` pour la validation, sans trace de pile ni requête SQL.
- [ ] Limites de débit par tenant, par utilisateur et par jeton, plus une limite globale. Réponse 429 avec `Retry-After`.
- [ ] Opérations en masse avec résultat ligne par ligne, et le mode (tout ou rien, ou partiel) choisi explicitement.
- [ ] Versionnement dans l'URL ou par en-tête, dépréciation annoncée, inventaire des versions exposées.

### Webhooks sortants
- Format Standard Webhooks : en-têtes `webhook-id`, `webhook-timestamp`, `webhook-signature`. On signe `id.timestamp.corps`, de préférence en ed25519, sinon en HMAC-SHA256 avec un secret par endpoint et une rotation sans coupure (deux signatures pendant la transition).
- Charge mince (type d'événement et identifiants). Le destinataire relit la fiche par l'API, ce qui garde l'accès aux données personnelles contrôlé et audité.
- URL de destination contrôlée contre la SSRF :
  - HTTPS seulement, IP résolue validée puis connexion sur cette même IP ;
  - refus des plages privées, de bouclage et lien-local, de `169.254.169.254`, `fc00::/7` et `fe80::/10` ;
  - redirections non suivies, envoi par un proxy de sortie dans un sous-réseau isolé.
- Délai de 15 à 30 s, nouvelles tentatives sur plusieurs jours avec backoff exponentiel et jitter. Endpoint désactivé et admin prévenu après échecs prolongés. Journal des livraisons et rejeu manuel.

### Webhooks entrants et intégrations
- Signature vérifiée sur le corps brut, avant tout parse, avec comparaison en temps constant. Horodatage refusé au-delà de 5 minutes et identifiant d'événement dédoublonné.
- Les données reçues d'un tiers sont validées comme une saisie utilisateur (API10).
- Jetons OAuth des intégrations :
  - scopes minimaux, PKCE ;
  - refresh token chiffré au repos par chiffrement d'enveloppe (clé de données par tenant, clé maîtresse en KMS), jamais dans les journaux ni côté navigateur ;
  - rotation des refresh tokens, révocation à la déconnexion de l'intégration et au départ de l'utilisateur.

## 8. Synchro e-mail, agenda, mobile

- Synchro e-mail Gmail :
  - synchro complète au premier branchement, puis synchro partielle par `history.list` depuis le dernier `historyId` stocké ;
  - réponse 404 = synchro complète obligatoire ;
  - `users.watch` renouvelé avant 7 jours ; la notification déclenche une synchro, elle ne remplace pas le curseur.
- Microsoft 365 : delta par dossier ou par vue d'agenda, `deltaLink` stocké, abonnements renouvelés, `reauthorizationRequired` traité, 410 = resynchro complète.
- Rattachement automatique d'un e-mail aux fiches par adresse normalisée. Les domaines personnels (gmail.com...) ne créent pas de compte société.
- Le contenu des e-mails est une donnée personnelle de tiers : l'utilisateur choisit ce qui est synchronisé (exclusions par domaine, messages privés), et la conservation suit la fiche.
- Mobile et hors ligne (voir `android-dev`) :
  - file d'envoi locale durable, opérations idempotentes avec clé générée sur l'appareil ;
  - version envoyée avec chaque modification, fusion champ par champ quand les champs diffèrent ;
  - si le même champ a changé des deux côtés, conflit montré à l'utilisateur, jamais écrasé en silence ;
  - cache local chiffré, purgé à la déconnexion et à la révocation.

## 9. RGPD et CNIL

### Bases légales et prospection
- B2C par voie électronique : consentement préalable, case non précochée, distinct des CGU. Exception pour un client existant et des produits analogues, seulement s'il y a eu une vente réelle (un simple compte créé ne suffit pas).
- B2B : intérêt légitime si le message est lié à la profession, avec information et opposition simple dès la collecte. Les adresses génériques de société sont hors champ.
- Chaque message de prospection donne l'identité de l'émetteur et un moyen simple de se désinscrire, pris en compte tout de suite.
- Consentement stocké comme une preuve : personne, canal, finalité, date, source, version du texte affiché, retrait.

### Durées de conservation (référentiel CNIL « gestion des activités commerciales »)
| Donnée | Durée | Point de départ |
|---|---|---|
| Prospect non client | 3 ans | collecte ou dernier contact venant du prospect (un clic compte, une ouverture d'e-mail non) |
| Client, pour la prospection | relation commerciale + 3 ans | fin de la relation (achat, fin de garantie, fin de contrat, dernier contact du client) |
| Données du contrat après sa fin | archivage intermédiaire séparé, dans la limite de la prescription | fin du contrat |
| Liste d'opposition | au moins 3 ans, pour cette seule fin | date de l'opposition |
| Compte en ligne inactif | 2 ans, avec un avertissement avant | dernière action de la personne |
| Devis sans suite | 1 an | émission du devis |
| Justificatif d'identité pour un droit | supprimé dès la demande traitée | réponse |
| Journaux techniques | 6 mois à 1 an (recommandation CNIL) | événement |

Les durées du devis et des journaux viennent de pages CNIL lues seulement par extrait : à revérifier avant de les citer à un client.

- [ ] Une tâche planifiée applique ces durées : relance avant échéance pour les prospects, puis suppression ou archivage. Elle est testée avec une horloge contrôlée.
- [ ] Tout écart au référentiel est justifié par écrit (le référentiel n'est pas contraignant, mais l'écart doit se justifier).

### Droits des personnes
- Réponse sous un mois, prolongeable de deux mois pour une demande complexe, en prévenant la personne dans le premier mois.
- Accès : export de tout ce qui concerne la personne (fiches, activités, consentements, historique), dans un format lisible.
- Portabilité : seulement pour les traitements fondés sur le consentement ou le contrat, en format structuré lisible par machine (JSON, CSV).
- Effacement : suppression réelle et propagée (section 2.4), sauf obligation légale ou besoin de preuve en justice documentés. L'identité minimale nécessaire au respect de l'opposition reste dans la liste d'opposition.
- Opposition : effet immédiat sur toutes les campagnes et automatisations, et vérifiée à chaque import.

### Documentation
- Registre des traitements, mentions d'information, contrat de sous-traitance (article 28) avec chaque sous-traitant (hébergeur, envoi d'e-mails, téléphonie).
- AIPD dès que 2 des 9 critères CEPD sont réunis : scoring ou notation, décision automatisée, grande échelle, croisement de données, personnes vulnérables...
- Sécurité (art. 32) : voir section 10 et le guide sécurité CNIL (journalisation protégée, sauvegardes 3-2-1 avec restauration testée, algorithmes à jour).

## 10. Sécurité propre au CRM

Le socle est `security-gate` (ASVS 5.0 niveau 2 partout, niveau 3 pour l'authentification, les sessions, l'OAuth des
intégrations et les données personnelles). En plus, pour un CRM :
- [ ] ASVS V8 appliqué en entier : 8.1.1 et 8.1.2 (règles écrites jusqu'au champ), 8.2.2 (BOLA), 8.2.3 (BOPLA), 8.3.1 (contrôle serveur), 8.3.2 (révocation immédiate), 8.3.3 (droits de l'appelant d'origine), 8.4.1 (inter-tenant).
- [ ] SSO (OIDC ou SAML) par tenant, MFA obligatoire pour les admins et proposé à tous, provisioning SCIM si besoin, session révoquée au départ d'un utilisateur.
- [ ] Notes et modèles d'e-mail en texte riche :
  - assainis côté serveur à l'enregistrement et côté client à l'affichage (DOMPurify, liste blanche de balises et d'attributs, aucune modification après assainissement) ;
  - CSP stricte, pas de `javascript:` dans les liens ;
  - variables de modèle échappées selon le contexte (HTML, URL, en-tête d'e-mail, contre l'injection d'en-têtes).
- [ ] Pièces jointes : type vérifié par le contenu, taille plafonnée, antivirus, stockage par tenant, servies avec `Content-Disposition: attachment` et depuis un domaine séparé.
- [ ] Recherche : le filtre de droits est appliqué dans la requête d'index, jamais après coup sur une page de résultats. Les compteurs ne trahissent pas les fiches invisibles.
- [ ] Rapports et tableaux de bord : les agrégats respectent les droits de fiche et de champ. Un total ne doit pas révéler un montant masqué.
- [ ] Flux sensibles protégés contre l'abus automatisé (API6) : export, envoi d'e-mails en masse, invitations, import.
- [ ] Chiffrement en transit (TLS 1.2 minimum, 1.3 de préférence) et au repos. Chiffrement applicatif des champs très sensibles, avec une clé par tenant si le contrat l'exige.
- [ ] Journal d'audit : connexions, échecs, changements de droits, exports, fusions, suppressions, accès admin plateforme. Ajout seul, lecture limitée au tenant, aucune donnée personnelle en clair dans les journaux techniques.
- [ ] Secrets d'intégration et de webhook jamais renvoyés en clair après création : affichés une seule fois, puis seulement leurs derniers caractères.

## 11. Performance et exploitation

- Index composites qui commencent par `tenant_id`. Partitionnement par tenant ou par date pour l'audit et les activités dès que le volume l'exige.
- Listes et kanban paginés par curseur, colonnes chargées à la demande, nombre total estimé quand il coûte cher.
- Recherche dans un moteur séparé, indexé en asynchrone avec une file « à indexer » remplie au commit, un index ou un filtre par tenant, une recherche de repli en base si l'index est indisponible.
- Calculs lourds (totaux, scoring, recalcul de droits, imports) en tâches de fond, idempotentes, avec quotas par tenant.
- Gouverneurs par tenant : temps de requête maximal, nombre d'automatisations en chaîne (avec détection de boucle), appels sortants.
- Surveiller l'asymétrie de données : propriétaire ou parent au-delà de 10 000 fiches.
- Observabilité : traces avec tenant et identifiant de requête (sans donnée personnelle), métriques par tenant (latence, erreurs, file d'attente), alerte sur les refus inter-tenant répétés.
- Sauvegardes 3-2-1, restauration testée régulièrement, y compris la restauration d'un seul tenant. Voir `devops-ci`.

## 12. Stratégie de test

Le cadre vient de `feature-test-pipeline` (risques, techniques, unitaire puis fonctionnel puis régression) et de
`qa-e2e` (Cypress en priorité, Playwright au besoin, sélecteurs, isolation, données). Le verdict, c'est `validation-gate`.
Zéro échec : un test instable se répare, il ne se met pas en quarantaine et ne passe pas grâce à une relance.

### Par niveau
- **Unitaire** : calculs (prévision pondérée, totaux de devis, conversion de devise), normalisation (e-mail, téléphone, domaine), règles de correspondance de doublons, neutralisation CSV, validation des champs personnalisés, machine à états du cycle de vie.
- **Intégration (vraie base PostgreSQL, pas de mock)** :
  - RLS et rôle applicatif, inventaire des tables tiré du schéma ;
  - repository filtré par tenant ;
  - tâches de fond (import, rétention, effacement) ;
  - index de recherche mis à jour puis purgé.
- **Contrat** : schéma OpenAPI vérifié contre les réponses réelles, format RFC 9457, signatures de webhooks contre les vecteurs de test de la spec.
- **E2E** : parcours métier ci-dessous, données créées par l'API avant chaque test, un tenant par worker pour paralléliser sans collision.
- **Sécurité dynamique** : voir `security-gate` 3.3, plus les cas de la liste ci-dessous.
- **Performance** : jeu de données réaliste (par exemple 1 million de contacts, 10 tenants de tailles très inégales, un propriétaire proche de 10 000 fiches), avec un objectif de latence sur la liste, la recherche, le kanban et l'export.

### Matrice de permissions
- Générée depuis le document de politique : chaque rôle x objet x action x portée x champ sensible donne un résultat attendu.
- Chaque case est testée côté API, autorisée et refusée. L'interface est testée en plus (bouton absent ET API qui refuse), jamais à la place de l'API.
- Toute nouvelle permission ou tout nouvel objet sans ligne dans la matrice fait échouer la CI.

### Parcours à couvrir obligatoirement
1. Lead créé, qualifié, converti en contact, compte et opportunité, sans doublon créé.
2. Opportunité qui passe toutes les étapes jusqu'à gagnée. La prévision et le tableau de bord bougent comme prévu, et l'historique d'étape est complet.
3. Opportunité perdue : motif obligatoire, sortie de la prévision.
4. Import CSV en `;` avec BOM, accents, guillemets et retours à la ligne dans un champ, lignes invalides, doublons internes et contre la base. Le rapport est exact ligne par ligne et la liste d'opposition est respectée.
5. Détection de doublon à la création, puis fusion : enfants rattachés, opposition conservée, audit présent, annulation possible.
6. Export CSV avec des valeurs piégées (`=1+2`, `+cmd`, `-2+3`, `@SUM`, tabulation, CR, LF, `＝`). Aucune cellule n'est interprétée comme formule.
7. Commercial A qui tente de lire, modifier, exporter et chercher une fiche de B hors de sa portée : 404 ou 403 selon la règle, et rien ne fuit dans la recherche, les compteurs ou les suggestions de doublons.
8. Utilisateur du tenant 1 avec l'identifiant d'une fiche du tenant 2, sur chaque route et chaque méthode : 404. Même test en passant un faux `X-Tenant-ID`.
9. Affectation en masse : `owner_id`, `tenant_id`, `version`, champ protégé ou champ inconnu dans le corps, tous ignorés ou refusés.
10. Champ masqué (montant, par exemple) absent de la fiche, de la liste, de l'export, de la recherche, des rapports et des webhooks.
11. Retrait de droit pendant une session : refusé dès la requête suivante.
12. Demande d'accès puis d'effacement RGPD : export complet, puis plus aucune trace en base, dans l'index, le cache ou les exports stockés. La liste d'opposition garde le minimum.
13. Rétention : prospect sans contact depuis 3 ans relancé puis supprimé, avec une horloge contrôlée (pas d'attente réelle).
14. Webhook sortant vers `http://169.254.169.254`, `http://localhost`, une IP privée, un domaine qui se résout en IP privée, une redirection : tout est refusé.
15. Webhook entrant avec une signature fausse, un horodatage de plus de 5 minutes, puis le même identifiant rejoué : refusés, aucun effet de bord.
16. Note en texte riche avec `<img onerror>`, `<svg onload>`, `javascript:`, puis affichage dans la timeline, l'aperçu e-mail et l'export : rien ne s'exécute.
17. Synchro e-mail : curseur expiré (404 Gmail, 410 Graph) qui déclenche une synchro complète sans perte ni doublon.
18. Hors ligne : la même fiche modifiée sur deux appareils, champs différents fusionnés, même champ présenté en conflit.
19. Création avec la même `Idempotency-Key` envoyée deux fois : une seule fiche. Même clé avec un autre corps : erreur.
20. Limite de débit d'un tenant atteinte sans effet sur un autre tenant.

### Données de test
- Fabriques par entité, avec des valeurs uniques par test (suffixe aléatoire) et un tenant neuf par fichier de test ou par worker.
- Jeu « hostile » réutilisable : noms avec apostrophes et accents, formules, HTML, émojis, très longues chaînes, adresses e-mail limites.
- Aucune donnée réelle de client, même anonymisée à la main, dans les fixtures ni dans les captures d'écran.

## 13. Checklist de revue et definition of done

- [ ] Règles d'accès écrites jusqu'au champ, et matrice de tests à jour.
- [ ] Chaque requête est filtrée par tenant au niveau de la base (RLS ou schéma) et du dépôt. Le rôle applicatif ne contourne pas la RLS.
- [ ] Aucune entrée liée directement à une entité. DTO avec liste blanche de champs.
- [ ] Sorties filtrées par droits de champ partout : API, export, recherche, rapports, webhooks.
- [ ] Pagination, filtres, tris, idempotence, limites de débit et erreurs RFC 9457 en place sur chaque nouvelle route de liste ou de création.
- [ ] Export neutralisé contre les formules, et audité.
- [ ] URL sortantes protégées contre la SSRF, webhooks signés et vérifiés.
- [ ] Texte riche assaini, CSP active.
- [ ] Secrets et jetons chiffrés, absents des journaux.
- [ ] Base légale, durée de conservation et effacement traités pour toute nouvelle donnée personnelle. Registre mis à jour.
- [ ] Historique et audit sur les champs sensibles touchés.
- [ ] Tests unitaires, d'intégration et E2E des parcours concernés au vert du premier coup, sans relance, sur le SHA de tête.
- [ ] Verdict SEC-GO de `security-gate` et GO de `validation-gate`.
- [ ] Commit simple, description naturelle, rien n'est poussé ni fusionné sans l'accord explicite du propriétaire du projet.

## Sources

- OWASP ASVS 5.0, V8 Authorization : https://raw.githubusercontent.com/OWASP/ASVS/v5.0.0/5.0/en/0x17-V8-Authorization.md
- OWASP API Security Top 10 2023 : https://owasp.org/API-Security/editions/2023/en/0x11-t10/
- OWASP Multi-Tenant Security Cheat Sheet : https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html
- OWASP Mass Assignment Cheat Sheet : https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html
- OWASP SSRF Prevention Cheat Sheet : https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- OWASP CSV Injection : https://owasp.org/www-community/attacks/CSV_Injection
- Standard Webhooks 1.0 : https://raw.githubusercontent.com/standard-webhooks/standard-webhooks/main/spec/standard-webhooks.md
- HubSpot, validation des webhooks : https://developers.hubspot.com/docs/api/webhooks/validating-requests
- HubSpot, étapes de cycle de vie : https://knowledge.hubspot.com/records/use-lifecycle-stages
- Google AIP-158 Pagination : https://google.aip.dev/158
- Stripe, requêtes idempotentes : https://docs.stripe.com/api/idempotent_requests
- RFC 9457 Problem Details : https://www.rfc-editor.org/rfc/rfc9457.html
- Salesforce, architecture multitenant : https://architect.salesforce.com/fundamentals/platform-multitenant-architecture
- Salesforce, asymétrie de propriété : https://developer.salesforce.com/docs/atlas.en-us.draes.meta/draes/draes_group_membership_data_skew.htm
- Microsoft Dataverse, sécurité par propriété : https://learn.microsoft.com/en-us/power-platform/admin/wp-security-cds
- Gmail API, synchronisation : https://developers.google.com/workspace/gmail/api/guides/sync
- CNIL, prospection par voie électronique : https://www.cnil.fr/fr/la-prospection-commerciale-par-courrier-electronique
- CNIL, référentiel gestion des activités commerciales : https://cnil.fr/sites/cnil/files/atoms/files/referentiel_traitements-donnees-caractere-personnel_gestion-activites-commerciales.pdf
- CNIL, questions-réponses sur les référentiels : https://www.cnil.fr/fr/questions-reponses-sur-les-referentiels-relatifs-la-gestion-des-activites-commerciales-et-des

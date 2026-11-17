---
name: xlsx
description: >-
  Lire, créer ou modifier un classeur .xlsx, .xlsm ou .csv. Formules Excel, recalcul LibreOffice. Déclencheurs : tableur, xlsx, csv, openpyxl.
---

# Tableurs

openpyxl sert à créer, modifier et mettre en forme. `markitdown` donne un aperçu, sans coordonnées de cellules. pandas n'est pas installé ici : un gros volume passe par openpyxl ou le module `csv`. Installer un paquet seulement si l'auteur le demande.

Un classeur déjà là garde ses noms de feuilles, ses formules et sa mise en forme. Les chemins viennent de la demande.

## Écriture

- Une cellule calculée reçoit une formule (`=SUM(B2:B9)`). Un total déjà calculé en Python ne prend pas la place de la formule.
- `load_workbook` sans option renvoie les formules. `data_only=True` renvoie le cache, et cet objet n'a plus les formules. Ne pas enregistrer un classeur ouvert ainsi.
- Juste après un enregistrement openpyxl, le cache est vide. Le relire ne prouve rien tant que LibreOffice n'a pas recalculé.
- Fichier `.xlsm` : `keep_vba=True`, sinon l'enregistrement enlève les macros.
- Cellule fusionnée : écrire seulement l'ancre en haut à gauche.
- Un nom de feuille qui contient un espace se cite entre quotes : `='Nom de feuille'!B2`.

## Recalcul

LibreOffice est `/usr/bin/soffice`.

```bash
soffice --headless --convert-to xlsx --outdir DOSSIER FICHIER.xlsx
```

La commande écrit une copie dans `DOSSIER`. Remplacer l'original par cette copie après un succès. Si le classeur pointe vers un autre fichier, garder l'original : LibreOffice casse souvent ces liens.

Relire avec `data_only=True`. Une cellule `#REF!`, `#NAME?`, `#VALUE!`, `#DIV/0!`, `#N/A` ou `#NULL!` est à corriger.

`XLOOKUP`, `FILTER`, `UNIQUE`, `SORT` et `SEQUENCE` tombent souvent en erreur avec ce LibreOffice. Préférer `INDEX`/`MATCH`, `SUMIFS`, `IFERROR`. `TEXTJOIN`, `CONCAT`, `IFS`, `SWITCH`, `MAXIFS` et `MINIFS` s'écrivent avec le préfixe `_xlfn.` dans le fichier.

## Contrôle

Vérifier deux ou trois formules (bonne plage, bonne feuille), puis lancer le recalcul. Un classeur sans erreur LibreOffice peut quand même viser la mauvaise colonne.

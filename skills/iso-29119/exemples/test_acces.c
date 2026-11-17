#include <stddef.h>
#include <stdio.h>
#include "test_acces.h"

static const t_cas	g_cas[] = {
{"limite mode 0777 valide", {5, 5, 5, 5, 0777, LIRE}, 1},
{"limite mode 01000 invalide", {5, 5, 5, 5, 01000, LIRE}, -E_INVAL},
{"limite voulu 0 invalide", {5, 5, 5, 5, 0644, 0}, -E_INVAL},
{"limite voulu 8 invalide", {5, 5, 5, 5, 0644, 8}, -E_INVAL},
{"limite voulu 7 valide", {5, 5, 5, 5, 0700, 7}, 1},
{"table root lit mode 0", {0, 0, 5, 5, 0, LIRE}, 1},
{"table root ecrit mode 0", {0, 0, 5, 5, 0, ECRIRE}, 1},
{"table root execute sans bit x", {0, 0, 5, 5, 0644, EXECUTER}, 0},
{"table root execute avec un bit x", {0, 0, 5, 5, 0100, EXECUTER}, 1},
{"table proprietaire lit 0400", {5, 9, 5, 7, 0400, LIRE}, 1},
{"table proprietaire ecrit 0444", {5, 9, 5, 7, 0444, ECRIRE}, 0},
{"table groupe lit 0040", {6, 7, 5, 7, 0040, LIRE}, 1},
{"table groupe lit 0400", {6, 7, 5, 7, 0400, LIRE}, 0},
{"table autre lit 0004", {6, 8, 5, 7, 0004, LIRE}, 1},
{"table autre lit 0440", {6, 8, 5, 7, 0440, LIRE}, 0},
{"partition tous les bits voulus", {5, 9, 5, 7, 0600, LIRE | ECRIRE}, 1},
{"partition un bit manquant", {5, 9, 5, 7, 0400, LIRE | ECRIRE}, 0},
{"erreur proprietaire aussi du groupe", {5, 7, 5, 7, 0070, LIRE}, 0},
};

static int	verifier(const t_cas *c)
{
	int	obtenu;

	obtenu = acces_permis(c->d);
	if (obtenu == c->attendu)
	{
		printf("[ok] %s\n", c->nom);
		return (0);
	}
	printf("[ko] %s : %d au lieu de %d\n", c->nom, obtenu, c->attendu);
	return (1);
}

int	main(void)
{
	size_t	i;
	int		ko;

	i = 0;
	ko = 0;
	while (i < sizeof(g_cas) / sizeof(g_cas[0]))
	{
		ko += verifier(&g_cas[i]);
		i++;
	}
	if (ko != 0)
		printf("FAIL %d\n", ko);
	else
		printf("PASS %zu cas\n", i);
	return (ko != 0);
}

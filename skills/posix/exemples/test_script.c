#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "ecrire_tout.h"
#include "test_script.h"

static t_pas	g_script[8];
static size_t	g_pas;
static char		g_recu[16];
static size_t	g_recus;

static ssize_t	faux_write(int fd, const void *tampon, size_t taille)
{
	t_pas	pas;

	(void)fd;
	pas = g_script[g_pas];
	g_pas++;
	if (pas.retour < 0)
	{
		errno = pas.erreur;
		return (-1);
	}
	if ((size_t)pas.retour > taille)
		pas.retour = (ssize_t)taille;
	memcpy(g_recu + g_recus, tampon, (size_t)pas.retour);
	g_recus += (size_t)pas.retour;
	return (pas.retour);
}

static ssize_t	jouer(const t_pas *script, size_t n, size_t taille)
{
	memset(g_recu, 0, sizeof(g_recu));
	memcpy(g_script, script, n * sizeof(t_pas));
	g_pas = 0;
	g_recus = 0;
	errno = 0;
	return (ecrire_tout_avec(1, "abcde", taille, faux_write));
}

static int	verifier(const char *nom, int ok)
{
	if (ok)
		printf("[ok] %s\n", nom);
	else
		printf("[ko] %s\n", nom);
	return (!ok);
}

static int	cas_interruptions(void)
{
	const t_pas	eintr_puis_tout[] = {{-1, EINTR}, {5, 0}};
	const t_pas	partiels[] = {{2, 0}, {-1, EINTR}, {3, 0}};
	const t_pas	zero[] = {{2, 0}, {0, 0}};
	int			ko;

	ko = verifier("EINTR puis tout", jouer(eintr_puis_tout, 2, 5) == 5
			&& memcmp(g_recu, "abcde", 5) == 0);
	ko += verifier("partiel, EINTR, reste", jouer(partiels, 3, 5) == 5
			&& memcmp(g_recu, "abcde", 5) == 0 && g_pas == 3);
	ko += verifier("zero octet ecrit : compte court",
			jouer(zero, 2, 5) == 2);
	return (ko);
}

int	main(void)
{
	const t_pas	eagain[] = {{-1, EAGAIN}};
	int			ko;

	ko = cas_interruptions();
	ko += verifier("EAGAIN rendu a l appelant",
			jouer(eagain, 1, 5) == -1 && errno == EAGAIN);
	ko += verifier("taille nulle, aucun appel",
			jouer(eagain, 0, 0) == 0 && g_pas == 0);
	ko += verifier("taille au-dela de SSIZE_MAX",
			jouer(eagain, 0, (size_t)SIZE_MAX) == -1 && errno == EINVAL
			&& g_pas == 0);
	if (ko)
		printf("FAIL\n");
	else
		printf("PASS\n");
	return (ko != 0);
}

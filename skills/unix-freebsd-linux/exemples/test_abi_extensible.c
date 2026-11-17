#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include "abi_extensible.h"

static unsigned char	g_user[64];

static int	lire_faux_user(void *dst, uintptr_t src, size_t taille)
{
	uintptr_t	debut;

	debut = (uintptr_t)g_user;
	if (src < debut || taille > sizeof(g_user)
		|| src - debut > sizeof(g_user) - taille)
		return (-E_FAULT);
	memcpy(dst, (const void *)src, taille);
	return (0);
}

static t_source	source(size_t taille)
{
	t_source	s;

	s.adresse = (uintptr_t)g_user;
	s.taille = taille;
	s.lire = lire_faux_user;
	return (s);
}

static int	verifier(const char *nom, int obtenu, int attendu)
{
	if (obtenu == attendu)
	{
		printf("[ok] %s\n", nom);
		return (0);
	}
	printf("[ko] %s : %d au lieu de %d\n", nom, obtenu, attendu);
	return (1);
}

static int	cas_tailles(void)
{
	t_ouvrir	o;
	int			ko;

	memset(g_user, 0, sizeof(g_user));
	g_user[0] = 1;
	memset(&o, 0xff, sizeof(o));
	ko = verifier("v0 acceptee", lire_ouvrir(&o, source(16)), 0);
	ko += verifier("v0 completee par des zeros", o.resolution == 0, 1);
	ko += verifier("plus courte que v0", lire_ouvrir(&o, source(8)), -E_INVAL);
	ko += verifier("plus longue, queue nulle",
			lire_ouvrir(&o, source(40)), 0);
	g_user[39] = 1;
	ko += verifier("plus longue, queue non nulle",
			lire_ouvrir(&o, source(40)), -E_2BIG);
	ko += verifier("taille absurde",
			lire_ouvrir(&o, source(8192)), -E_2BIG);
	return (ko);
}

int	main(void)
{
	t_ouvrir	o;
	t_source	hors;
	uint64_t	resolution;
	int			ko;

	ko = cas_tailles();
	memset(g_user, 0, sizeof(g_user));
	resolution = RESOUDRE_SOUS | RESOUDRE_SANS_LIEN;
	memcpy(g_user + offsetof(t_ouvrir, resolution), &resolution, 8);
	ko += verifier("resolution connue", lire_ouvrir(&o, source(24)), 0);
	resolution = 0x4;
	memcpy(g_user + offsetof(t_ouvrir, resolution), &resolution, 8);
	ko += verifier("resolution inconnue",
			lire_ouvrir(&o, source(24)), -E_INVAL);
	hors = source(24);
	hors.adresse += 48;
	ko += verifier("hors espace user", lire_ouvrir(&o, hors), -E_FAULT);
	if (ko != 0)
		printf("FAIL\n");
	else
		printf("PASS\n");
	return (ko != 0);
}

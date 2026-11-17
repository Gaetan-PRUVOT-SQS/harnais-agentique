#include <stddef.h>
#include "verif.h"

#define DEBORDEMENT 32
#define DECALAGE_INVALIDE 40

void	verif_canari(void)
{
	char			tampon[8];
	volatile char	*p;
	volatile size_t	i;

	p = tampon;
	i = 0;
	while (i < DEBORDEMENT)
	{
		p[i] = 'A';
		i++;
	}
}

void	verif_ubsan(void)
{
	volatile int	decalage;
	volatile int	resultat;

	decalage = DECALAGE_INVALIDE;
	resultat = 1 << decalage;
	(void)resultat;
}

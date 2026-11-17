#include "abi_extensible.h"

#define TAILLE_MAX_STRUCT 4096u

int	drapeaux_valides(uint64_t drapeaux, uint64_t connus)
{
	if (drapeaux & ~connus)
		return (-E_INVAL);
	return (0);
}

static int	queue_a_zero(t_source src, size_t debut)
{
	unsigned char	morceau[64];
	size_t			n;
	size_t			i;

	while (debut < src.taille)
	{
		n = src.taille - debut;
		if (n > sizeof(morceau))
			n = sizeof(morceau);
		if (src.lire(morceau, src.adresse + debut, n) != 0)
			return (-E_FAULT);
		i = 0;
		while (i < n)
		{
			if (morceau[i] != 0)
				return (-E_2BIG);
			i++;
		}
		debut += n;
	}
	return (0);
}

static void	mettre_a_zero(unsigned char *p, size_t taille)
{
	while (taille > 0)
	{
		taille--;
		p[taille] = 0;
	}
}

int	copier_struct_user(void *dst, size_t taille_noyau, t_source src)
{
	size_t	commune;
	int		r;

	commune = src.taille;
	if (commune > taille_noyau)
	{
		r = queue_a_zero(src, taille_noyau);
		if (r != 0)
			return (r);
		commune = taille_noyau;
	}
	if (src.lire(dst, src.adresse, commune) != 0)
		return (-E_FAULT);
	mettre_a_zero((unsigned char *)dst + commune, taille_noyau - commune);
	return (0);
}

int	lire_ouvrir(t_ouvrir *dst, t_source src)
{
	int	r;

	if (src.taille < OUVRIR_TAILLE_V0)
		return (-E_INVAL);
	if (src.taille > TAILLE_MAX_STRUCT)
		return (-E_2BIG);
	r = copier_struct_user(dst, sizeof(*dst), src);
	if (r != 0)
		return (r);
	return (drapeaux_valides(dst->resolution, RESOUDRE_CONNUS));
}

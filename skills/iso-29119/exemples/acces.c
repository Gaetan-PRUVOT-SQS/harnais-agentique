#include "acces.h"

static unsigned int	bits_de_classe(t_demande d)
{
	if (d.uid == d.proprietaire)
		return ((d.mode >> 6) & 07u);
	if (d.gid == d.groupe)
		return ((d.mode >> 3) & 07u);
	return (d.mode & 07u);
}

int	acces_permis(t_demande d)
{
	if (d.mode > MODE_MAX || d.voulu == 0
		|| d.voulu > (LIRE | ECRIRE | EXECUTER))
		return (-E_INVAL);
	if (d.uid == 0)
	{
		if ((d.voulu & EXECUTER) && (d.mode & 0111u) == 0)
			return (0);
		return (1);
	}
	return ((bits_de_classe(d) & d.voulu) == d.voulu);
}

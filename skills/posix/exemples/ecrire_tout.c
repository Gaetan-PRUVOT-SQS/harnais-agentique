#include <errno.h>
#include <limits.h>
#include <unistd.h>
#include "ecrire_tout.h"

ssize_t	ecrire_tout_avec(int fd, const void *tampon, size_t taille,
			t_ecrire ecrire)
{
	const unsigned char	*octets;
	size_t				fait;
	ssize_t				r;

	if (taille > SSIZE_MAX)
	{
		errno = EINVAL;
		return (-1);
	}
	octets = tampon;
	fait = 0;
	while (fait < taille)
	{
		r = ecrire(fd, octets + fait, taille - fait);
		if (r < 0 && errno != EINTR)
			return (-1);
		if (r == 0)
			break ;
		if (r > 0)
			fait += (size_t)r;
	}
	return ((ssize_t)fait);
}

ssize_t	ecrire_tout(int fd, const void *tampon, size_t taille)
{
	return (ecrire_tout_avec(fd, tampon, taille, write));
}

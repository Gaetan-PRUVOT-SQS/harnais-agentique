#include <errno.h>
#include <time.h>
#include <unistd.h>
#include "test_tube.h"

void	remplir(unsigned char *donnees, size_t taille)
{
	size_t	i;

	i = 0;
	while (i < taille)
	{
		donnees[i] = (unsigned char)(i & 0xff);
		i++;
	}
}

static int	motif_valide(const unsigned char *tampon, size_t n, size_t debut)
{
	size_t	i;

	i = 0;
	while (i < n)
	{
		if (tampon[i] != (unsigned char)((debut + i) & 0xff))
			return (0);
		i++;
	}
	return (1);
}

int	lire_lentement(int fd)
{
	unsigned char	tampon[4096];
	struct timespec	pause;
	size_t			total;
	ssize_t			r;

	pause.tv_sec = 0;
	pause.tv_nsec = 20000;
	total = 0;
	r = 1;
	while (r != 0)
	{
		r = read(fd, tampon, sizeof(tampon));
		if (r < 0 && errno != EINTR)
			return (1);
		if (r > 0 && !motif_valide(tampon, (size_t)r, total))
			return (1);
		if (r > 0)
			total += (size_t)r;
		nanosleep(&pause, NULL);
	}
	return (total != TAILLE_TUBE);
}

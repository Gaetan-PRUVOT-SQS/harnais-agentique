#ifndef ECRIRE_TOUT_H
# define ECRIRE_TOUT_H
# include <sys/types.h>

typedef ssize_t	(*t_ecrire)(int fd, const void *tampon, size_t taille);

ssize_t	ecrire_tout(int fd, const void *tampon, size_t taille);
ssize_t	ecrire_tout_avec(int fd, const void *tampon, size_t taille,
			t_ecrire ecrire);

#endif

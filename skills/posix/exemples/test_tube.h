#ifndef TEST_TUBE_H
# define TEST_TUBE_H
# include <stddef.h>

# define TAILLE_TUBE 4194304

void	remplir(unsigned char *donnees, size_t taille);
int		lire_lentement(int fd);

#endif

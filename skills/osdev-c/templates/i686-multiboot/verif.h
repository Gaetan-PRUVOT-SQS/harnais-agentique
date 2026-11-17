#ifndef VERIF_H
# define VERIF_H

# ifndef VERIF
#  define VERIF 0
# endif
# define VERIF_CANARI 1
# define VERIF_UBSAN 2

void	verif_canari(void);
void	verif_ubsan(void);

#endif

#ifndef ABI_EXTENSIBLE_H
# define ABI_EXTENSIBLE_H
# include <stddef.h>
# include <stdint.h>

# define E_INVAL 22
# define E_2BIG 7
# define E_FAULT 14

# define OUVRIR_TAILLE_V0 16u
# define RESOUDRE_SOUS 0x1u
# define RESOUDRE_SANS_LIEN 0x2u
# define RESOUDRE_CONNUS 0x3u

typedef int	(*t_lire_user)(void *dst, uintptr_t src, size_t taille);

typedef struct s_source
{
	uintptr_t	adresse;
	size_t		taille;
	t_lire_user	lire;
}	t_source;

typedef struct s_ouvrir
{
	uint64_t	drapeaux;
	uint64_t	mode;
	uint64_t	resolution;
}	t_ouvrir;

int	drapeaux_valides(uint64_t drapeaux, uint64_t connus);
int	copier_struct_user(void *dst, size_t taille_noyau, t_source src);
int	lire_ouvrir(t_ouvrir *dst, t_source src);

#endif

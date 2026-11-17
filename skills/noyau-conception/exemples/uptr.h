#ifndef UPTR_H
# define UPTR_H
# include <stddef.h>
# include <stdint.h>

# define USER_DEBUT 0x00400000u
# define USER_FIN 0xC0000000u

typedef struct s_uptr
{
	uintptr_t	adresse;
}	t_uptr;

int	uptr_plage_valide(t_uptr p, size_t taille);
int	copier_depuis_user(void *dst, t_uptr src, size_t taille);
int	copier_vers_user(t_uptr dst, const void *src, size_t taille);

#endif

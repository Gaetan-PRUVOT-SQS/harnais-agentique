#include "uptr.h"

int	uptr_plage_valide(t_uptr p, size_t taille)
{
	uintptr_t	fin;

	if (__builtin_add_overflow(p.adresse, taille, &fin))
		return (0);
	return (p.adresse >= USER_DEBUT && fin <= USER_FIN);
}

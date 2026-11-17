#ifndef TEST_ACCES_H
# define TEST_ACCES_H
# include "acces.h"

typedef struct s_cas
{
	const char	*nom;
	t_demande	d;
	int			attendu;
}	t_cas;

#endif

#ifndef ACCES_H
# define ACCES_H

# define LIRE 4u
# define ECRIRE 2u
# define EXECUTER 1u
# define MODE_MAX 0777u
# define E_INVAL 22

typedef struct s_demande
{
	unsigned int	uid;
	unsigned int	gid;
	unsigned int	proprietaire;
	unsigned int	groupe;
	unsigned int	mode;
	unsigned int	voulu;
}	t_demande;

int	acces_permis(t_demande d);

#endif

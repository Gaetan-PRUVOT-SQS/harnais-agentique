#ifndef VERROU_H
# define VERROU_H
# include <stdint.h>

# define EFLAGS_IF 0x200

typedef struct s_verrou
{
	uint8_t	pris;
}	t_verrou;

uint32_t	verrou_prendre(t_verrou *v);
void		verrou_rendre(t_verrou *v, uint32_t drapeaux);

#endif

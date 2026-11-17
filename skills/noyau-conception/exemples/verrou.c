#include "verrou.h"

uint32_t	verrou_prendre(t_verrou *v)
{
	uint32_t	drapeaux;

	drapeaux = __builtin_ia32_readeflags_u32();
	__asm__ volatile ("cli" : : : "memory");
	while (__atomic_test_and_set(&v->pris, __ATOMIC_ACQUIRE))
		__asm__ volatile ("pause");
	return (drapeaux);
}

void	verrou_rendre(t_verrou *v, uint32_t drapeaux)
{
	__atomic_clear(&v->pris, __ATOMIC_RELEASE);
	if (drapeaux & EFLAGS_IF)
		__asm__ volatile ("sti" : : : "memory");
}

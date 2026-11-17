#include "appel_systeme.h"

long	appel_systeme(long numero, long a, long b, long c)
{
	long	retour;

	__asm__ volatile ("int $0x80" : "=a" (retour)
		: "a" (numero), "b" (a), "c" (b), "d" (c) : "memory");
	return (retour);
}

#include "kassert.h"

void	kassert(int condition, const char *quoi)
{
	if (__builtin_expect(condition != 0, 1))
		return ;
	panic_a(quoi, (uintptr_t)__builtin_return_address(0));
}

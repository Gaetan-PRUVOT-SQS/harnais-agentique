#ifndef KASSERT_H
# define KASSERT_H
# include <stdint.h>

void	panic_a(const char *quoi, uintptr_t appelant) __attribute__((noreturn));
void	kassert(int condition, const char *quoi) __attribute__((noinline));

#endif

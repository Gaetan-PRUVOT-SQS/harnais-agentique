#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define GROS 4096

size_t		asm_strlen(const char *s);
uint64_t	bad_func(uint64_t x);
uint64_t	checked_call(void *fn, uint64_t a, uint64_t b, uint64_t c);
extern int	g_checked_call_clobbered;

static void	check_strlen(const char *s)
{
	uint64_t	got;

	got = checked_call((void *)asm_strlen, (uintptr_t)s, 0, 0);
	assert(got == strlen(s));
	assert(!g_checked_call_clobbered);
}

int	main(void)
{
	const char	*cas[] = {"", "a", "bonjour", "deux mots", "\x01\xff"};
	char		gros[GROS + 1];
	size_t		i;

	memset(gros, 'x', GROS);
	gros[GROS] = '\0';
	i = 0;
	while (i < sizeof(cas) / sizeof(*cas))
		check_strlen(cas[i++]);
	check_strlen(gros);
	checked_call((void *)bad_func, 7, 0, 0);
	assert(g_checked_call_clobbered);
	puts("asm_strlen OK, vérificateur ABI OK");
	return (0);
}

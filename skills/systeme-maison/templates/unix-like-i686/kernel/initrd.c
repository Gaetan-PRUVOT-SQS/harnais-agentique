#include <stdint.h>
#include "multiboot.h"

#define CPIO_MAGIC "070701"
#define CPIO_MAGIC_TAILLE 6

static int	commence_par(const char *texte, const char *prefixe)
{
	while (*prefixe)
	{
		if (*texte != *prefixe)
			return (0);
		texte++;
		prefixe++;
	}
	return (1);
}

int	initrd_verifier(const t_mb_info *info)
{
	const t_mb_module	*module;

	if ((info->flags & MB_INFO_MODULES) == 0 || info->mods_count == 0)
		return (0);
	module = (const t_mb_module *)(uintptr_t)info->mods_addr;
	if (module->fin <= module->debut + CPIO_MAGIC_TAILLE)
		return (0);
	return (commence_par((const char *)(uintptr_t)module->debut, CPIO_MAGIC));
}

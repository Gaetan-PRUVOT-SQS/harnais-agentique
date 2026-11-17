#ifndef MULTIBOOT_H
# define MULTIBOOT_H
# include <stdint.h>

# define MULTIBOOT_MAGIC 0x2BADB002
# define MB_INFO_MODULES 0x8

typedef struct s_mb_module
{
	uint32_t	debut;
	uint32_t	fin;
	uint32_t	chaine;
	uint32_t	reserve;
}	t_mb_module;

typedef struct s_mb_info
{
	uint32_t	flags;
	uint32_t	mem_lower;
	uint32_t	mem_upper;
	uint32_t	boot_device;
	uint32_t	cmdline;
	uint32_t	mods_count;
	uint32_t	mods_addr;
}	t_mb_info;

_Static_assert(sizeof(t_mb_module) == 16, "t_mb_module");
_Static_assert(sizeof(t_mb_info) == 28, "t_mb_info");

int	initrd_verifier(const t_mb_info *info);

#endif

#include <stdint.h>
#include "multiboot.h"
#include "panic.h"
#include "serial.h"

void	kmain(uint32_t magic, uint32_t info)
{
	serial_init();
	if (magic != MULTIBOOT_MAGIC)
		panic("mauvais magic multiboot");
	serial_puts("[ok] serie\n");
	if (!initrd_verifier((const t_mb_info *)(uintptr_t)info))
	{
		serial_puts("FAIL initrd absent ou pas en cpio newc\n");
		return ;
	}
	serial_puts("[ok] initrd\n");
	serial_puts("PASS\n");
}

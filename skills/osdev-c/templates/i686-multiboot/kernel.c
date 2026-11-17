#include <stdint.h>
#include <stddef.h>
#include "panic.h"
#include "serial.h"
#include "verif.h"

#define MULTIBOOT_MAGIC 0x2BADB002
#define VGA_BLANC 0x0F00

static void	vga_ecrire(const char *msg)
{
	volatile uint16_t	*vga;
	size_t				i;

	vga = (volatile uint16_t *)0xB8000;
	i = 0;
	while (msg[i])
	{
		vga[i] = (uint16_t)(VGA_BLANC | (uint8_t)msg[i]);
		i++;
	}
}

void	kmain(uint32_t magic, uint32_t info)
{
	(void)info;
	serial_init();
	if (magic != MULTIBOOT_MAGIC)
		panic("mauvais magic multiboot");
	vga_ecrire("OK");
	if (VERIF == VERIF_CANARI)
		verif_canari();
	if (VERIF == VERIF_UBSAN)
		verif_ubsan();
	serial_puts("kmain OK\n");
}

#include "gdt.h"

static inline void	outb(uint16_t port, uint8_t val)
{
	__asm__ volatile ("outb %0, %1" : : "a" (val), "Nd" (port) : "memory");
}

void	mmio_write(uintptr_t addr, uint32_t val)
{
	*(volatile uint32_t *)addr = val;
	outb(0x80, 0);
}

void	halt(void)
{
	while (1)
		__asm__ volatile ("cli; hlt");
}

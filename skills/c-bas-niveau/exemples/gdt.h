#ifndef GDT_H
# define GDT_H

# include <stdint.h>

# define PTE_PRESENT 0x1ull

typedef struct __attribute__((packed)) s_gdt_entry
{
	uint16_t	limit_low;
	uint16_t	base_low;
	uint8_t		base_mid;
	uint8_t		access;
	uint8_t		gran;
	uint8_t		base_high;
}	t_gdt_entry;

_Static_assert(sizeof(t_gdt_entry) == 8, "t_gdt_entry");

void	mmio_write(uintptr_t addr, uint32_t val);
void	halt(void) __attribute__((noreturn));

#endif

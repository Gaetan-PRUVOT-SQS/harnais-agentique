#include "panic.h"
#include "serial.h"

__attribute__((noreturn)) void	panic(const char *msg)
{
	serial_puts("PANIC: ");
	serial_puts(msg);
	serial_puts("\n");
	while (1)
		__asm__ volatile ("cli; hlt");
}

__attribute__((noreturn)) void	__stack_chk_fail(void)
{
	panic("canari de pile ecrase");
}

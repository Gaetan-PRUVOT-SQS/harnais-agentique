ENTRY(_start)

SECTIONS
{
	. = 0x400000;

	.text BLOCK(4K) : ALIGN(4K) { *(.text*) }
	.rodata BLOCK(4K) : ALIGN(4K) { *(.rodata*) }
	.note.gnu.build-id : ALIGN(4) { *(.note.gnu.build-id) }
	.data BLOCK(4K) : ALIGN(4K) { *(.data*) }
	.bss BLOCK(4K) : ALIGN(4K)
	{
		*(COMMON)
		*(.bss*)
	}
	/DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}

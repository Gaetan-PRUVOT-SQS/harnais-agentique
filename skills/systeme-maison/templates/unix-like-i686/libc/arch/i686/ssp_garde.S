	.section .data
	.align 4
	.global __stack_chk_guard
__stack_chk_guard:
	.long 0x000aff0d

	.section .note.GNU-stack, "", @progbits

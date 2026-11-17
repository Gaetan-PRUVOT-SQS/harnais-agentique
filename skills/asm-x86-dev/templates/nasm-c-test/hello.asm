default rel
section .rodata
msg:	db "hello sans libc", 10
len	equ $ - msg

section .text
global _start
_start:
	mov	eax, 1
	mov	edi, 1
	lea	rsi, [msg]
	mov	edx, len
	syscall
	mov	eax, 60
	xor	edi, edi
	syscall

section .note.GNU-stack noalloc noexec nowrite progbits

	.section .text
	.global _start
	.type _start, @function
_start:
	xor %ebp, %ebp
	mov (%esp), %eax
	lea 4(%esp), %ebx
	lea 4(%ebx, %eax, 4), %ecx
	and $-16, %esp
	sub $4, %esp
	push %ecx
	push %ebx
	push %eax
	call main
	add $16, %esp
	sub $12, %esp
	push %eax
	call exit
1:	jmp 1b

	.section .note.GNU-stack, "", @progbits

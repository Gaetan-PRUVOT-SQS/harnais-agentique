default rel
section .text
global asm_strlen:function (asm_strlen.end - asm_strlen)
asm_strlen:
	mov	rax, rdi
.loop:
	cmp	byte [rax], 0
	je	.done
	inc	rax
	jmp	.loop
.done:
	sub	rax, rdi
	ret
.end:

section .note.GNU-stack noalloc noexec nowrite progbits

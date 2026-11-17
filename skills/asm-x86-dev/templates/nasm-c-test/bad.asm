default rel
section .text
global bad_func:function (bad_func.end - bad_func)
bad_func:
	xor	ebx, ebx
	mov	rax, rdi
	ret
.end:
section .note.GNU-stack noalloc noexec nowrite progbits

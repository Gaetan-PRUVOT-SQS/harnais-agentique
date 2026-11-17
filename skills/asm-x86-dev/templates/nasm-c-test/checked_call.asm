default rel

%define CANARY(n) (0x5A5A5A5A00000000 + n)

section .bss
global g_checked_call_clobbered:data 4
g_checked_call_clobbered:	resd 1

section .text
global checked_call:function (checked_call.end - checked_call)
checked_call:
	push	rbx
	push	rbp
	push	r12
	push	r13
	push	r14
	push	r15
	sub	rsp, 8
	mov	rax, rdi
	mov	rdi, rsi
	mov	rsi, rdx
	mov	rdx, rcx
	mov	rbx, CANARY(1)
	mov	rbp, CANARY(2)
	mov	r12, CANARY(3)
	mov	r13, CANARY(4)
	mov	r14, CANARY(5)
	mov	r15, CANARY(6)
	call	rax
	xor	ecx, ecx
	mov	rdx, CANARY(1)
	cmp	rbx, rdx
	setne	cl
	%assign i 2
	%rep 5
		mov	rdx, CANARY(i)
		%if i == 2
			cmp	rbp, rdx
		%else
			cmp	r%eval(i + 9), rdx
		%endif
		setne	dl
		or	cl, dl
		%assign i i + 1
	%endrep
	mov	[g_checked_call_clobbered], ecx
	add	rsp, 8
	pop	r15
	pop	r14
	pop	r13
	pop	r12
	pop	rbp
	pop	rbx
	ret
.end:

section .note.GNU-stack noalloc noexec nowrite progbits

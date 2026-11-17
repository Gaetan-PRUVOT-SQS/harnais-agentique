bits 16
org 0x7C00
	jmp 0:start
start:
	xor ax, ax
	mov ds, ax
	xchg bx, bx
	mov si, msg
.next:
	lodsb
	test al, al
	jz .halt
	out 0xE9, al
	jmp .next
.halt:
	cli
	hlt
	jmp .halt
msg db "bochs OK", 10, 0
times 510-($-$$) db 0
dw 0xAA55

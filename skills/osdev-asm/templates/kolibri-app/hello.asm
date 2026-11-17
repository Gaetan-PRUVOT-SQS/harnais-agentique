format binary as ""
use32
org 0x0

	db 'MENUET01'
	dd 0x01
	dd START
	dd I_END
	dd MEM
	dd STACKTOP
	dd 0, 0

include 'macros.inc'

START:
redraw:
	call	draw_window
wait_event:
	mcall	10
	cmp	eax, 1
	je	redraw
	cmp	eax, 2
	je	key
	cmp	eax, 3
	je	button
	jmp	wait_event

key:
	mcall	2
	jmp	wait_event

button:
	mcall	17
	cmp	ah, 1
	jne	wait_event
	mcall	-1

draw_window:
	mcall	12, 1
	mcall	0, <100, 300>, <100, 120>, 0x34FFFFFF, , title
	mcall	4, <20, 30>, 0x90000000, msg
	mcall	12, 2
	ret

title	db 'hello', 0
msg	db 'Bonjour depuis FASM', 0

I_END:
	rb	4096
align 16
STACKTOP:
MEM:

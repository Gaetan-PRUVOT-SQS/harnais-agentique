BOCHS ?= $(shell command -v bochs-debugger || echo bochs)
BOCHS_DBG ?= $(shell timeout 5 $(BOCHS) --help 2>&1 | grep -q -- '-debugger ' && echo -debugger)
VGABIOS ?= $(firstword $(wildcard /usr/share/bochs/VGABIOS-lgpl-latest.bin /usr/share/bochs/VGABIOS-lgpl-latest))
export VGABIOS

all: floppy.img

boot.bin: boot.asm
	nasm -f bin $< -o $@
	test "$$(stat -c %s $@)" = 512

floppy.img: boot.bin
	dd if=/dev/zero of=$@ bs=512 count=2880 status=none
	dd if=$< of=$@ conv=notrunc status=none

test: floppy.img
	timeout 10 $(BOCHS) -q $(BOCHS_DBG) -f bochsrc -rc cmds.bochs > bochs.out 2>&1 || true
	grep -a "bochs OK" bochs.out && grep -a "0000:7c0b" bochs.out

qemu: floppy.img
	timeout 5 qemu-system-i386 -drive format=raw,if=floppy,file=floppy.img \
		-display none -debugcon stdio -no-reboot || true

clean:
	rm -f boot.bin floppy.img bochs.out bochs.log

.PHONY: all test qemu clean

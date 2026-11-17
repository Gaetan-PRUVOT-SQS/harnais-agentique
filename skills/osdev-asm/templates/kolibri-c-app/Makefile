KOS_SDK     ?= $(HOME)/Bureau/osdev/kolibrios-ports/sdk
KOLIBRI_SRC ?= $(HOME)/Bureau/osdev/kolibrios
KOLIBRI_IMG ?= $(HOME)/Bureau/osdev/kolibri.img
CC           = $(KOS_SDK)/bin/i586-kolibrios-gcc
export PATH := $(KOS_SDK)/bin:$(PATH)
CFLAGS       = -Os -Wall -Wextra -Werror
APP          = hello
NAME         = HELLOC
EXPECT       = Bonjour depuis C (16 octets)

all: $(APP)

$(APP): $(APP).c
	$(CC) $(CFLAGS) $< -o $@

kernel-com1.mnt: $(KOLIBRI_SRC)/kernel/trunk/kernel.asm
	cd $(KOLIBRI_SRC)/kernel/trunk && test -f lang.inc || echo 'lang fix en_US' > $(KOLIBRI_SRC)/kernel/trunk/lang.inc
	cd $(KOLIBRI_SRC)/kernel/trunk && fasm -m 262144 -ddebug_com_base=0x3f8 kernel.asm $(CURDIR)/$@
	kerpack $@ $@

test.img: $(APP) kernel-com1.mnt $(KOLIBRI_IMG)
	cp $(KOLIBRI_IMG) $@
	mcopy -o -i $@ kernel-com1.mnt ::KERNEL.MNT
	mdel -i $@ ::GAMES/PIPES
	mcopy -o -i $@ $(APP) ::$(NAME)
	mtype -i $@ ::SETTINGS/AUTORUN.DAT > autorun.dat
	printf '/SYS/$(NAME) "" 0\n' >> autorun.dat
	mcopy -o -i $@ autorun.dat ::SETTINGS/AUTORUN.DAT

test:
	@test -x $(CC) || { echo "tests non lancés : SDK KolibriOS absent ($(KOS_SDK))"; exit 3; }
	$(MAKE) test.img
	rm -f serial.log
	timeout 30 qemu-system-i386 -m 256 -fda test.img -boot a -display none \
		-serial file:serial.log -no-reboot -accel kvm || true
	grep -a "$(EXPECT)" serial.log && echo "appli C OK"

run: test.img
	qemu-system-i386 -m 256 -fda test.img -boot a -serial stdio -accel kvm

clean:
	rm -f $(APP) kernel-com1.mnt test.img autorun.dat serial.log

.PHONY: all test run clean

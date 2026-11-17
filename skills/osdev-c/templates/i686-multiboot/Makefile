TOOLCHAIN ?= gcc
PROFIL    ?= debug
VERIF     ?= 0

B       = build/$(PROFIL)-v$(VERIF)
KERNEL  = $(B)/kernel.elf
OBJ     = $(addprefix $(B)/,boot.o serial.o panic.o verif.o kernel.o)

DURCI   = -fstack-protector-strong -ftrivial-auto-var-init=zero \
          -fzero-call-used-regs=used-gpr -fno-delete-null-pointer-checks \
          -Wframe-larger-than=1024 -Wvla
ifeq ($(PROFIL),debug)
DURCI  += -fsanitize=undefined -fsanitize-trap=undefined
else ifeq ($(PROFIL),release)
DURCI  += -fno-strict-overflow
else
$(error PROFIL vaut debug ou release)
endif

CFLAGS  = -std=gnu11 -ffreestanding -fno-pic -mno-sse -mno-mmx -mno-80387 \
          -O2 -g -fno-omit-frame-pointer -Wall -Wextra -Werror \
          -MMD -MP -DVERIF=$(VERIF) $(DURCI)

ifeq ($(TOOLCHAIN),gcc)
CC      = i686-elf-gcc
LD      = i686-elf-gcc
LDFLAGS = -T linker.ld -ffreestanding -nostdlib -O2 -Wl,-z,noexecstack -Wl,--build-id=sha1
LIBS    = -lgcc
else
CC      = clang --target=i686-elf
LD      = ld -m elf_i386
LDFLAGS = -T linker.ld -nostdlib -z noexecstack --build-id=sha1
LIBS    =
endif

QEMU    = qemu-system-i386 -kernel $(KERNEL) -display none -no-reboot

all: $(KERNEL)

$(KERNEL): $(OBJ) linker.ld
	$(LD) $(LDFLAGS) -o $@ $(OBJ) $(LIBS)

$(B)/%.o: %.c | $(B)
	$(CC) $(CFLAGS) -c $< -o $@

$(B)/%.o: %.S | $(B)
	$(CC) $(CFLAGS) -c $< -o $@

$(B):
	mkdir -p $@

-include $(OBJ:.o=.d)

run: $(KERNEL)
	qemu-system-i386 -kernel $(KERNEL) -serial stdio -no-reboot -no-shutdown \
		-d int,cpu_reset -D $(B)/qemu.log

test:
	@$(MAKE) --no-print-directory PROFIL=debug demarre
	@$(MAKE) --no-print-directory PROFIL=release demarre
	@$(MAKE) --no-print-directory PROFIL=release VERIF=1 canari
	@$(MAKE) --no-print-directory PROFIL=debug VERIF=2 piege

demarre: $(KERNEL)
	@timeout 5 $(QEMU) -serial stdio | grep -q "kmain OK" \
		&& echo "boot OK ($(PROFIL))" || (echo "boot KO ($(PROFIL))"; exit 1)

canari: $(KERNEL)
	@timeout 3 $(QEMU) -serial stdio | grep -q "PANIC: canari" \
		&& echo "canari OK" || (echo "canari KO"; exit 1)

piege: $(KERNEL)
	@timeout 3 $(QEMU) -serial null -d int -D $(B)/qemu.log; \
	grep -q "v=06" $(B)/qemu.log && echo "piege UBSan OK" || (echo "piege UBSan KO"; exit 1)

debug: $(KERNEL)
	qemu-system-i386 -kernel $(KERNEL) -serial stdio -no-reboot -s -S &
	gdb -ex 'symbol-file $(KERNEL)' -ex 'target remote :1234' -ex 'break kmain' -ex 'continue'

debug-batch: $(KERNEL)
	qemu-system-i386 -kernel $(KERNEL) -display none -serial file:$(B)/serial.log -no-reboot -s -S & \
	pid=$$!; sleep 0.5; \
	timeout 20 gdb -batch -q -ex 'file $(KERNEL)' -ex 'target remote :1234' \
		-ex 'break kmain' -ex 'continue' $(GDB_CMDS) -ex 'kill'; \
	kill $$pid 2>/dev/null; true

clean:
	rm -rf build

.PHONY: all run test demarre canari piege debug debug-batch clean

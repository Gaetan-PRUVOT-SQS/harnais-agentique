PROFIL    ?= debug
CC         = i686-elf-gcc
AR         = i686-elf-ar
NM         = i686-elf-nm
READELF    = i686-elf-readelf
B          = build/$(PROFIL)
INC_CC    := $(shell $(CC) -print-file-name=include)

DURCI      = -fstack-protector-strong -ftrivial-auto-var-init=zero \
             -fzero-call-used-regs=used-gpr -fno-delete-null-pointer-checks \
             -Wframe-larger-than=1024 -Wvla
ifeq ($(PROFIL),debug)
DURCI     += -fsanitize=undefined -fsanitize-trap=undefined
else ifeq ($(PROFIL),release)
DURCI     += -fno-strict-overflow
else
$(error PROFIL vaut debug ou release)
endif

COMMUN     = -std=gnu11 -ffreestanding -fno-pic -mno-sse -mno-mmx -mno-80387 \
             -O2 -g -fno-omit-frame-pointer -Wall -Wextra -Werror -MMD -MP $(DURCI)
CFLAGS_USER = $(COMMUN) -nostdinc -isystem libc/include -isystem $(B)/include \
              -isystem $(INC_CC) -Iabi -Ilibc -fno-builtin -fno-tree-loop-distribute-patterns

NOYAU_OBJ  = $(addprefix $(B)/kernel/,boot.o serial.o panic.o initrd.o kernel.o)
LIBC_OBJ   = $(addprefix $(B)/libc/,unistd.o stdlib.o string.o ssp.o errno.o \
             appel_systeme.o ssp_garde.o errno_messages.o)
CRT0       = $(B)/libc/crt0.o
PROGRAMMES = $(B)/initrd/init

all: $(B)/disque.img

$(B)/kernel.elf: $(NOYAU_OBJ) kernel/linker.ld
	$(CC) -T kernel/linker.ld -ffreestanding -nostdlib -O2 -Wl,-z,noexecstack \
		-Wl,--build-id=sha1 -o $@ $(NOYAU_OBJ) -lgcc

$(B)/kernel/%.o: kernel/%.c | $(B)/kernel
	$(CC) $(COMMUN) -c $< -o $@

$(B)/kernel/%.o: kernel/%.S | $(B)/kernel
	$(CC) $(COMMUN) -c $< -o $@

$(B)/include/errno.h: abi/errno.liste outils/genere-errno
	sh outils/genere-errno abi/errno.liste $(B)/include

$(B)/include/errno_messages.c: $(B)/include/errno.h

$(B)/include/sys/types.h: abi/types.liste outils/genere-types
	sh outils/genere-types abi/types.liste $(B)/include

ENTETES_GENERES = $(B)/include/errno.h $(B)/include/sys/types.h

$(B)/libc/errno_messages.o: $(B)/include/errno_messages.c | $(B)/libc
	$(CC) $(CFLAGS_USER) -c $< -o $@

$(B)/libc/%.o: libc/%.c $(ENTETES_GENERES) | $(B)/libc
	$(CC) $(CFLAGS_USER) -c $< -o $@

$(B)/libc/%.o: libc/arch/i686/%.c $(ENTETES_GENERES) | $(B)/libc
	$(CC) $(CFLAGS_USER) -c $< -o $@

$(B)/libc/%.o: libc/arch/i686/%.S | $(B)/libc
	$(CC) $(CFLAGS_USER) -c $< -o $@

$(B)/libc/%.o: libc/%.S | $(B)/libc
	$(CC) $(CFLAGS_USER) -c $< -o $@

$(B)/libc/libc.a: $(LIBC_OBJ)
	rm -f $@
	$(AR) rcsD $@ $^

$(B)/user/%.o: user/%.c $(ENTETES_GENERES) | $(B)/user
	$(CC) $(CFLAGS_USER) -c $< -o $@

$(B)/initrd/%: $(B)/user/%.o $(CRT0) $(B)/libc/libc.a user/linker.ld | $(B)/initrd
	$(CC) -T user/linker.ld -nostdlib -static -Wl,-z,noexecstack -Wl,-z,separate-code \
		-Wl,--build-id=sha1 -o $@ $(CRT0) $< $(B)/libc/libc.a

$(B)/disque.img: $(B)/kernel.elf $(PROGRAMMES) $(shell find racine -type f)
	image-disque --noyau $(B)/kernel.elf --racine racine --initrd $(B)/initrd \
		--sortie $@ --nom unix-like

$(B)/kernel $(B)/libc $(B)/user $(B)/initrd:
	mkdir -p $@

-include $(NOYAU_OBJ:.o=.d) $(LIBC_OBJ:.o=.d) $(CRT0:.o=.d) $(B)/user/init.d

verif-user: $(PROGRAMMES)
	@for p in $(PROGRAMMES); do \
		test -z "$$($(NM) -u $$p)" || { echo "symboles indéfinis dans $$p"; exit 1; }; \
		LC_ALL=C $(READELF) -h $$p | grep -q 'Type:.*EXEC' || { echo "$$p : pas un ELF exécutable"; exit 1; }; \
	done
	@echo "programmes utilisateur OK ($(PROFIL)) : liés sans libgcc, aucun symbole indéfini"

demarre-bios: $(B)/disque.img
	@qemu-test --disque $< --arch i386 --attendu PASS --echec FAIL --delai 60 \
		--journal $(B)/qemu-test/bios.log

demarre-uefi: $(B)/disque.img
	@qemu-test --disque $< --arch x86_64 --uefi --attendu PASS --echec FAIL --delai 60 \
		--journal $(B)/qemu-test/uefi.log

verifier: verif-user demarre-bios demarre-uefi

licences:
	@licences-tierces --licence-projet GPL-2.0-or-later

posix: $(ENTETES_GENERES)
	@verifier-posix errno abi/errno.liste
	@verifier-posix entetes libc/include $(B)/include

test:
	@$(MAKE) --no-print-directory PROFIL=debug verifier
	@$(MAKE) --no-print-directory PROFIL=release verifier
	@$(MAKE) --no-print-directory posix
	@$(MAKE) --no-print-directory licences

clean:
	rm -rf build

.PHONY: all verif-user demarre-bios demarre-uefi verifier licences posix test clean

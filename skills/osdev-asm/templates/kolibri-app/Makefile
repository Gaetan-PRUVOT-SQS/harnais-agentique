KOLIBRI_SRC ?= $(HOME)/Bureau/osdev/kolibrios
KOLIBRI_IMG ?= $(HOME)/Bureau/osdev/kolibri.img
IMG_URL      = https://builds.kolibrios.org/en_US/data/data/kolibri.img
APP          = hello
NAME         = HELLO

all: $(APP)

$(APP): $(APP).asm
	INCLUDE=$(KOLIBRI_SRC)/programs fasm -m 65536 $< $@

$(KOLIBRI_IMG):
	curl -fL -o $@ $(IMG_URL)

test.img: $(APP) $(KOLIBRI_IMG)
	cp $(KOLIBRI_IMG) $@
	mcopy -o -i $@ $(APP) ::$(NAME)
	mtype -i $@ ::SETTINGS/AUTORUN.DAT > autorun.dat
	printf '/SYS/$(NAME) "" 0\n' >> autorun.dat
	mcopy -o -i $@ autorun.dat ::SETTINGS/AUTORUN.DAT

test:
	@test -f $(KOLIBRI_SRC)/programs/macros.inc || { echo "tests non lancés : sources KolibriOS absentes ($(KOLIBRI_SRC))"; exit 3; }
	$(MAKE) $(APP)
	test "$$(head -c 8 $(APP))" = MENUET01 && echo "en-tête OK"

run: test.img
	qemu-system-i386 -m 256 -fda test.img -boot a -accel kvm

shot: test.img
	(sleep 35; echo "screendump shot.ppm"; sleep 2; echo quit) | \
		timeout 60 qemu-system-i386 -m 256 -fda test.img -boot a \
		-display none -monitor stdio -no-reboot -accel kvm >/dev/null 2>&1
	python3 -c "from PIL import Image; Image.open('shot.ppm').save('shot.png')"
	rm -f shot.ppm

clean:
	rm -f $(APP) test.img autorun.dat shot.png shot.ppm

.PHONY: all test run shot clean

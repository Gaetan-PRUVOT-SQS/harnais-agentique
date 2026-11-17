CFLAGS := -std=c17 -D_POSIX_C_SOURCE=202405L -Wall -Wextra -Werror -pedantic -g -O1 \
	-fsanitize=address,undefined -fno-sanitize-recover=all
BUILD := build

test: $(BUILD)/test_script $(BUILD)/test_tube
	./$(BUILD)/test_script
	./$(BUILD)/test_tube
	shellcheck -S info pipefail.sh
	checkbashisms -p pipefail.sh
	@for s in dash 'bash --posix'; do \
		$$s pipefail.sh >/dev/null; \
		test $$? -eq 1 || { echo "pipefail ignoré par $$s"; exit 1; }; \
	done; echo 'pipefail actif sous dash et bash --posix'

$(BUILD)/test_script: ecrire_tout.c test_script.c ecrire_tout.h test_script.h | $(BUILD)
	$(CC) $(CFLAGS) ecrire_tout.c test_script.c -o $@

$(BUILD)/test_tube: ecrire_tout.c tube_lecteur.c test_tube.c ecrire_tout.h test_tube.h | $(BUILD)
	$(CC) $(CFLAGS) ecrire_tout.c tube_lecteur.c test_tube.c -o $@ $(LDLIBS)

$(BUILD):
	mkdir -p $@

clean:
	rm -rf $(BUILD)

.PHONY: test clean

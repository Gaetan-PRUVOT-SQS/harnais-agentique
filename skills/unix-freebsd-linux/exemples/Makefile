CFLAGS := -std=c17 -Wall -Wextra -Werror -O1 -g \
	-fsanitize=address,undefined -fno-sanitize-recover=all
BUILD := build
SRCS := abi_extensible.c test_abi_extensible.c

test: $(BUILD)/test_abi_extensible
	./$(BUILD)/test_abi_extensible
	mandoc -T lint -W style ouvrir.2

$(BUILD)/test_abi_extensible: $(SRCS) abi_extensible.h | $(BUILD)
	$(CC) $(CFLAGS) $(SRCS) -o $@

$(BUILD):
	mkdir -p $@

clean:
	rm -rf $(BUILD)

.PHONY: test clean

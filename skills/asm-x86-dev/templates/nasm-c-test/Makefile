NASM    = nasm -f elf64 -g -F dwarf -Werror
CC      = gcc
CFLAGS  = -g -Wall -Wextra -Werror -fsanitize=address,undefined

ASM_OBJ = strlen.o checked_call.o bad.o

all: test_strlen hello

%.o: %.asm
	$(NASM) $< -o $@

test_strlen: test_strlen.c $(ASM_OBJ)
	$(CC) $(CFLAGS) $^ -o $@

hello: hello.o
	ld $< -o $@

test: test_strlen hello
	./test_strlen
	./hello | grep -q "hello sans libc" && echo "hello OK"

clean:
	rm -f *.o test_strlen hello

.PHONY: all test clean

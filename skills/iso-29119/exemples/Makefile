CFLAGS := -std=c17 -Wall -Wextra -Werror -g
SAN := -O1 -fsanitize=address,undefined -fno-sanitize-recover=all
GCC := gcc
COUV := -O0 --coverage -fprofile-abs-path -fcondition-coverage
BUILD := build
SRCS := acces.c test_acces.c
HDRS := acces.h test_acces.h

verifier: test couverture tests-outil

test: $(BUILD)/san/test_acces
	./$(BUILD)/san/test_acces

couverture: $(BUILD)/couv/test_acces
	rm -f $(BUILD)/couv/*.gcda
	./$(BUILD)/couv/test_acces
	cd $(BUILD)/couv && LC_ALL=C gcov -b -g -o . acces.o > resume.txt
	./verifier-couverture $(BUILD)/couv/resume.txt 100

tests-outil:
	shellcheck -S info verifier-couverture
	bats tests

$(BUILD)/san/test_acces: $(SRCS) $(HDRS) | $(BUILD)/san
	$(CC) $(CFLAGS) $(SAN) $(SRCS) -o $@

$(BUILD)/couv/acces.o: acces.c acces.h | $(BUILD)/couv
	$(GCC) $(CFLAGS) $(COUV) -c acces.c -o $@

$(BUILD)/couv/test_acces.o: test_acces.c $(HDRS) | $(BUILD)/couv
	$(GCC) $(CFLAGS) -O0 -c test_acces.c -o $@

$(BUILD)/couv/test_acces: $(BUILD)/couv/acces.o $(BUILD)/couv/test_acces.o
	$(GCC) --coverage $^ -o $@

$(BUILD)/san $(BUILD)/couv:
	mkdir -p $@

clean:
	rm -rf $(BUILD)

.PHONY: verifier test couverture tests-outil clean

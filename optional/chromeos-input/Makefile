CC ?= gcc
CFLAGS = -O2 -Wall -Wextra -Werror

all: workbench-input

workbench-input: input.c
	$(CC) -static $(CFLAGS) -o $@ $<

check:
	mkdir -p build
	$(CC) $(CFLAGS) -o build/test_input test_input.c
	./build/test_input
	python3 -m unittest -v test_desktop
	bash -n start.sh install-host.sh

clean:
	rm -rf build workbench-input

.PHONY: all check clean

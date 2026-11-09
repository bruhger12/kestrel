.PHONY: all build clean test

all: build

build:
	$(MAKE) -C engine

clean:
	$(MAKE) -C engine clean

test:
	powershell -NoProfile -ExecutionPolicy Bypass -File tests/uci-smoke.ps1

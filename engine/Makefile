.PHONY: build datagen clean aarch64 cross-aarch64 cross-aarch64-clang

EXE := kestrel
SOURCES := src/patricia.cpp src/fathom/src/tbprobe.c

CXX ?= g++
CXXFLAGS := -O3 -march=x86-64-v3 -std=c++20 -ffast-math
LINKER :=

ifeq ($(OS), Windows_NT)
	DETECTED_OS := Windows
	SUFFIX := .exe
	CXXFLAGS += -static -static-libgcc -static-libstdc++
else
	DETECTED_OS := $(shell uname -s)
	LINKER := -lm
	CXXFLAGS += -pthread
	SUFFIX :=
endif

OUT := $(EXE)$(SUFFIX)

# --- Native build ----------------------------------------------------------
build: $(SOURCES)
	$(CXX) $^ $(CXXFLAGS) -o $(OUT) $(LINKER)

default: build

clean:
	rm -f $(OUT) data

datagen: datagen/datagen.cpp
	$(CXX) $^ $(CXXFLAGS) -o data $(LINKER)

# --- Native AArch64 build (on ARM host) -----------------------------------
aarch64: CXX := clang++
aarch64: CXXFLAGS := -O3 -std=c++20 -ffast-math -mcpu=native -pthread -static-libstdc++ -static-libgcc
aarch64: OUT := $(EXE)_aarch64$(SUFFIX)
aarch64: $(SOURCES)
	$(CXX) $^ $(CXXFLAGS) -o $(OUT) $(LINKER)

# --- Cross-compile for AArch64 (fully static) -----------------------------
# Usage: make cross-aarch64 CROSS=aarch64-linux-gnu
cross-aarch64: CROSS ?= aarch64-linux-gnu
cross-aarch64: CXX := $(CROSS)-g++
cross-aarch64: CXXFLAGS := -O3 -std=c++20 -ffast-math -march=armv8-a -pthread -static -static-libstdc++ -static-libgcc
cross-aarch64: OUT := $(EXE)_aarch64$(SUFFIX)
cross-aarch64: $(SOURCES)
	$(CXX) $(CXXFLAGS) $^ -o $(OUT)

# --- Cross-compile for AArch64 using clang (requires proper sysroot) -----
cross-aarch64-clang: CXX := clang++
cross-aarch64-clang: CXXFLAGS := --target=aarch64-linux-gnu -O3 -std=c++20 -ffast-math -march=armv8-a -pthread -static
cross-aarch64-clang: OUT := $(EXE)_aarch64$(SUFFIX)
cross-aarch64-clang: $(SOURCES)
	$(CXX) $(CXXFLAGS) $^ -o $(OUT)

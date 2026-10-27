SIM ?= ghdl
TOPLEVEL_LANG = vhdl
VHDL_SOURCES = $(abspath ../../src/counter.vhd)
TOPLEVEL = counter
COCOTB_TEST_MODULES = test_counter

include $(shell cocotb-config --makefiles)/Makefile.sim

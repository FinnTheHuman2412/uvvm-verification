.PHONY: test-uart clean

test-uart:
	@bash scripts/run_uart_demo.sh > build/uart_demo.log 2>&1
	@tail -n 20 build/uart_demo.log

clean:
	rm -rf build

.PHONY: test-cosim

test-cosim:
	@bash scripts/run_uart_cosim.sh > build/uart_cosim.log 2>&1
	@tail -n 25 build/uart_cosim.log

.PHONY: regression

regression:
	@bash benchmarks/run_regression.sh

.PHONY: test-uart clean

test-uart:
	@bash scripts/run_uart_demo.sh > build/uart_demo.log 2>&1
	@tail -n 20 build/uart_demo.log

clean:
	rm -rf build

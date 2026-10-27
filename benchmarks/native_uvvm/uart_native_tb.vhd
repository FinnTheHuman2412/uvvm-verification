library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library uvvm_util;
context uvvm_util.uvvm_util_context;

library uvvm_vvc_framework;
use uvvm_vvc_framework.ti_vvc_framework_support_pkg.all;

library bitvis_vip_uart;
use bitvis_vip_uart.vvc_methods_pkg.all;
use bitvis_vip_uart.td_vvc_framework_common_methods_pkg.all;

library bitvis_vip_sbi;
use bitvis_vip_sbi.vvc_methods_pkg.all;
use bitvis_vip_sbi.td_vvc_framework_common_methods_pkg.all;

library bitvis_vip_clock_generator;
context bitvis_vip_clock_generator.vvc_context;

entity uart_native_tb is
  generic (G_N : positive := 5);
end entity;

architecture sim of uart_native_tb is
  constant C_CLK_PERIOD : time := 10 ns;
  constant C_BIT_PERIOD : time := 16 * C_CLK_PERIOD;
  constant C_ADDR_RX_DATA : unsigned(2 downto 0) := "000";

  type t_bytes is array (natural range <>) of std_logic_vector(7 downto 0);
  constant C_TEST_VALUES : t_bytes := (
    x"A5", x"55", x"AA", x"00", x"FF"
  );
begin

  -- Reuse the same UART DUT and UVVM VVC harness.
  i_harness : entity work.uart_vvc_demo_th;

  p_test : process
  begin
    await_uvvm_initialization(VOID);

    start_clock(CLOCK_GENERATOR_VVCT, 1, "Start UART clock");

    wait for 10 * C_CLK_PERIOD;

    shared_uart_vvc_config(TX, 1).bfm_config.bit_time :=
      C_BIT_PERIOD;

    shared_uart_vvc_config(RX, 1).bfm_config.bit_time :=
      C_BIT_PERIOD;

    -- Equivalent five-byte verification workload.
    for i in 0 to G_N - 1 loop
      uart_transmit(
        UART_VVCT, 1, TX, C_TEST_VALUES(i mod C_TEST_VALUES'length), "Native UART TX"
      );

      await_completion(UART_VVCT, 1, TX, 13 * C_BIT_PERIOD);

      wait for 200 ns;

      sbi_check(
        SBI_VVCT, 1, C_ADDR_RX_DATA,
        C_TEST_VALUES(i mod C_TEST_VALUES'length), "Native RX_DATA"
      );

      await_completion(SBI_VVCT, 1, 13 * C_BIT_PERIOD);
    end loop;

    report "NATIVE_UVVM_BENCHMARK_COMPLETED" severity note;

    std.env.stop;
    wait;
  end process;

end architecture;

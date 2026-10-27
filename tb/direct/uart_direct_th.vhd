library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity uart_direct_th is
  port (
    clk   : in std_logic := '0';
    arst  : in std_logic := '1';

    cs    : in std_logic := '0';
    addr  : in unsigned(2 downto 0) := (others => '0');
    wr    : in std_logic := '0';
    rd    : in std_logic := '0';
    wdata : in std_logic_vector(7 downto 0) := (others => '0');
    rdata : out std_logic_vector(7 downto 0);

    rx_a  : in std_logic := '1';
    tx    : out std_logic
  );
end entity;

architecture sim of uart_direct_th is
begin

  i_uart : entity work.uart
    generic map (
      GC_CLOCKS_PER_BIT => 16,
      GC_MIN_EQUAL_SAMPLES_PER_BIT => 15
    )
    port map (
      clk   => clk,
      arst  => arst,
      cs    => cs,
      addr  => addr,
      wr    => wr,
      rd    => rd,
      wdata => wdata,
      rdata => rdata,
      rx_a  => rx_a,
      tx    => tx
    );

end architecture;

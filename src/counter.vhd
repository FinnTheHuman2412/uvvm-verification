library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity counter is
  port (
    clk   : in  std_logic;
    rst   : in  std_logic;
    count : out unsigned(7 downto 0)
  );
end entity;

architecture rtl of counter is
  signal value : unsigned(7 downto 0) := (others => '0');
begin
  process(clk)
  begin
    if rising_edge(clk) then
      if rst = '1' then
        value <= (others => '0');
      else
        value <= value + 1;
      end if;
    end if;
  end process;

  count <= value;
end architecture;

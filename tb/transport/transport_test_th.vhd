library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity transport_test_th is
  port (
    req_valid : in  std_logic;
    req_op    : in  std_logic_vector(3 downto 0);
    req_addr  : in  unsigned(4 downto 0);
    req_data  : in  std_logic_vector(15 downto 0);
    rsp_busy  : out std_logic := '0';
    rsp_done  : out std_logic := '0'
  );
end entity;

architecture rtl of transport_test_th is
begin
  process
  begin
    loop
      wait until req_valid = '1';

      rsp_busy <= '1';
      rsp_done <= '0';

      wait for 10 ns;

      rsp_busy <= '0';
      rsp_done <= '1';

      wait until req_valid = '0';
      rsp_done <= '0';
    end loop;
  end process;
end architecture;

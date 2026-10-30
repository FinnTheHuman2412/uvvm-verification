library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
library uvvm_util;
context uvvm_util.uvvm_util_context;
library uvvm_vvc_framework;
use uvvm_vvc_framework.ti_vvc_framework_support_pkg.all;
library bitvis_vip_sbi;
use bitvis_vip_sbi.sbi_bfm_pkg.all;
use bitvis_vip_sbi.vvc_methods_pkg.all;
use bitvis_vip_sbi.td_vvc_framework_common_methods_pkg.all;

entity generic_vvc_th is
  generic (
    G_COMMAND_TIMEOUT_NS : positive := 1000;
    G_CHECK_ALERT_LEVEL : t_alert_level := ERROR
  );
  port (
    cmd_valid : in std_logic;
    cmd_vvc_type : in unsigned(3 downto 0);
    cmd_instance : in unsigned(7 downto 0);
    cmd_operation : in unsigned(7 downto 0);
    cmd_addr : in unsigned(15 downto 0);
    cmd_data : in std_logic_vector(31 downto 0);
    cmd_ready : out std_logic := '0';
    cmd_busy : out std_logic := '0';
    cmd_done : out std_logic := '0';
    cmd_status : out std_logic_vector(1 downto 0) := "00"
  );
end entity;

architecture sim of generic_vvc_th is
  signal clk : std_logic := '0';
  type t_interfaces is array(1 to 2) of t_sbi_if(
    addr(15 downto 0), wdata(31 downto 0), rdata(31 downto 0));
  signal bus_if : t_interfaces;
  -- Scalar observations of physical target writes, independent of bridge routing.
  signal target1_active, target2_active : std_logic;
  signal target1_write_count, target2_write_count : natural := 0;
  signal target1_last_addr, target2_last_addr : unsigned(15 downto 0);
  signal target1_last_data, target2_last_data : std_logic_vector(31 downto 0);
begin
  clk <= not clk after 5 ns;
  target1_active <= bus_if(1).cs;
  target2_active <= bus_if(2).cs;
  engine : entity uvvm_vvc_framework.ti_uvvm_engine;
  targets : for i in 1 to 2 generate
    -- Each VVC owns a separate interface and a separate register bank.
    type t_memory is array(0 to 65535) of std_logic_vector(31 downto 0);
    signal memory : t_memory := (others => (others => '0'));
    signal write_count : natural := 0;
    signal last_addr : unsigned(15 downto 0) := (others => '0');
    signal last_data : std_logic_vector(31 downto 0) := (others => '0');
  begin
    observe_first : if i = 1 generate
      target1_write_count <= write_count;
      target1_last_addr <= last_addr;
      target1_last_data <= last_data;
    end generate;
    observe_second : if i = 2 generate
      target2_write_count <= write_count;
      target2_last_addr <= last_addr;
      target2_last_data <= last_data;
    end generate;
    vvc : entity bitvis_vip_sbi.sbi_vvc
      generic map(GC_ADDR_WIDTH => 16, GC_DATA_WIDTH => 32, GC_INSTANCE_IDX => i)
      port map(clk => clk, sbi_vvc_master_if => bus_if(i));
    bus_if(i).ready <= '1';
    bus_if(i).rdata <= memory(to_integer(bus_if(i).addr)) when
      not is_x(std_logic_vector(bus_if(i).addr)) else (others => '0');
    registers : process(clk)
    begin
      if rising_edge(clk) then
        if bus_if(i).cs = '1' and bus_if(i).wena = '1' then
          memory(to_integer(bus_if(i).addr)) <= bus_if(i).wdata;
          write_count <= write_count + 1;
          last_addr <= bus_if(i).addr;
          last_data <= bus_if(i).wdata;
        end if;
      end if;
    end process;
  end generate;

  bridge : process
    variable instance : natural;
    variable errors, tb_errors, failures, tb_failures : natural;
    variable target : unsigned(3 downto 0);
    variable operation, selected_instance : unsigned(7 downto 0);
    variable address : unsigned(15 downto 0);
    variable data : std_logic_vector(31 downto 0);
    variable result : std_logic_vector(1 downto 0);
    variable faulted : boolean := false;
  begin
    await_uvvm_initialization(VOID);
    -- Alerts are returned to Python through the command status.
    set_alert_stop_limit(ERROR, 0);
    set_alert_stop_limit(TB_ERROR, 0);
    set_alert_stop_limit(FAILURE, 0);
    set_alert_stop_limit(TB_FAILURE, 0);
    wait for 100 ns;
    cmd_ready <= '1';
    loop
      if cmd_valid /= '1' then
        wait until cmd_valid = '1';
      end if;
      target := cmd_vvc_type;
      selected_instance := cmd_instance;
      operation := cmd_operation;
      address := cmd_addr;
      data := cmd_data;
      cmd_busy <= '1';
      result := "00";
      errors := get_alert_counter(ERROR);
      tb_errors := get_alert_counter(TB_ERROR);
      failures := get_alert_counter(FAILURE);
      tb_failures := get_alert_counter(TB_FAILURE);
      if faulted or (is_x(std_logic_vector(target)) or is_x(std_logic_vector(selected_instance)) or
         is_x(std_logic_vector(operation)) or is_x(std_logic_vector(address)) or is_x(data)) then
        result := "11";
        faulted := true;
      elsif target /= 1 or (selected_instance /= 1 and selected_instance /= 2) or
            (operation /= 1 and operation /= 2) then
        result := "10";
      else
        instance := to_integer(selected_instance);
        if operation = 1 then
          sbi_write(SBI_VVCT, instance, address, data, "Protocol v1 write");
        else
          sbi_check(SBI_VVCT, instance, address, data, "Protocol v1 check", alert_level => G_CHECK_ALERT_LEVEL);
        end if;
        await_completion(SBI_VVCT, instance, G_COMMAND_TIMEOUT_NS * 1 ns);
        if get_alert_counter(TB_ERROR) > tb_errors or
           get_alert_counter(TB_FAILURE) > tb_failures then
          result := "11";
          faulted := true;
        elsif get_alert_counter(ERROR) > errors or get_alert_counter(FAILURE) > failures then
          result := "01";
        end if;
      end if;
      if cmd_valid /= '1' or target /= cmd_vvc_type or selected_instance /= cmd_instance or
         operation /= cmd_operation or address /= cmd_addr or data /= cmd_data then
        result := "11";
        faulted := true;
      end if;
      cmd_status <= result;
      cmd_busy <= '0';
      cmd_done <= '1';
      if cmd_valid = '0' then
        -- A withdrawn request must still receive an observable error response.
        wait for 1 ns;
      else
        wait until cmd_valid = '0';
      end if;
      cmd_done <= '0';
    end loop;
  end process;
end architecture;

from cocotb.triggers import Timer, RisingEdge, with_timeout, Lock


class UVVMVerificationError(RuntimeError):
    """A UVVM alert was detected while executing a command."""


class CommandTransport:
    def __init__(self, dut, timeout_us=20, signals=None, require_status=False, extra_signals=None):
        self.dut = dut
        self._lock = Lock()
        self._faulted = False
        self._timeout_us = timeout_us

        names = {
            "valid": "cmd_valid",
            "opcode": "cmd_opcode",
            "address": "cmd_addr",
            "data": "cmd_data",
            "busy": "cmd_busy",
            "done": "cmd_done",
        }

        if signals is not None:
            unknown = set(signals) - set(names)
            if unknown:
                raise ValueError(f"Unknown signal mappings: {unknown}")
            names.update(signals)

        names.update(extra_signals or {})

        self.signals = {
            key: getattr(dut, name)
            for key, name in names.items()
        }

        # Optional verification-result output.
        self.status = getattr(dut, "cmd_status", None)
        if require_status and self.status is None:
            raise ValueError(
                "Required verification status signal 'cmd_status' is missing"
            )

        self.signals["valid"].value = 0
        self.signals["opcode"].value = 0
        self.signals["address"].value = 0
        self.signals["data"].value = 0

    async def _execute(self, opcode, address, value, **fields):
        async with self._lock:
            if self._faulted:
                raise RuntimeError(
                    "UVVM controller is faulted; restart the simulation"
                )

            data_max = (1 << len(self.signals["data"])) - 1
            address_max = (1 << len(self.signals["address"])) - 1
            opcode_max = (1 << len(self.signals["opcode"])) - 1

            if not 0 <= value <= data_max:
                raise ValueError(f"Data must be between 0 and {data_max}")

            if not 0 <= address <= address_max:
                raise ValueError(
                    f"Address must be between 0 and {address_max}"
                )

            if not 0 <= opcode <= opcode_max:
                raise ValueError(
                    f"Opcode must be between 0 and {opcode_max}"
                )

            for key, value_field in fields.items():
                if not 0 <= value_field < (1 << len(self.signals[key])):
                    raise ValueError(f"Invalid {key}: {value_field}")

            dut = self.dut

            try:
                assert int(self.signals["valid"].value) == 0

                for key, value_field in fields.items():
                    self.signals[key].value = value_field
                self.signals["opcode"].value = opcode
                self.signals["address"].value = address
                self.signals["data"].value = value
                self.signals["valid"].value = 1

                await with_timeout(
                    RisingEdge(self.signals["done"]),
                    self._timeout_us,
                    "us"
                )

                await Timer(1, unit="ns")
                assert int(self.signals["busy"].value) == 0

                status = int(self.status.value) if self.status is not None else 0

                self.signals["valid"].value = 0

                await Timer(1, unit="ns")
                assert int(self.signals["done"].value) == 0

                self._check_status(status, opcode)

            except UVVMVerificationError:
                # Verification failed, but the handshake completed.
                raise
            except BaseException:
                self._faulted = True
                raise


    def _check_status(self, status, opcode):
        if status:
            raise UVVMVerificationError(
                f"UVVM verification failed for opcode {opcode}"
            )

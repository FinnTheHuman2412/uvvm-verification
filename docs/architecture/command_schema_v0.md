# Command schema v0 — Python adapter over the existing VHDL bridge

Status: **prototype, not yet experimentally validated**.

## Purpose

Offer a typed Python API without changing `CommandTransport`,
`UVVMController`, or `uart_cosim_th.vhd`.

```python
from cosim.vvc_api import VVCAPI, VVCCommand, VVC, Operation

api = VVCAPI(dut)
await api.execute(VVCCommand(VVC.SBI, Operation.SBI_CHECK, address=3, data=1))
```

## Fields

- `vvc`: `UART` or `SBI`.
- `operation`: a supported operation (see table).
- `instance`: must be `1` in this version; any other value raises `ValueError`.
- `address`: unsigned 3-bit integer, default `0`.
- `data`: unsigned 8-bit integer, default `0`.

The fields above are **Python-level metadata**. They are translated
to existing bridge opcodes, not transferred as an independent command schema.

## Supported operations

| VVC | Operation | Opcode | Completion semantics |
| --- | --- | ---: | --- |
| UART | TRANSMIT_CHECK | 0 | UART TX completes; SBI RX register checked |
| SBI | WRITE_CHECK_UART | 1 | SBI write and UART RX expectation complete |
| SBI | CHECK | 2 | SBI check completes |
| UART | EXPECT | 3 | Receive expectation queued; **not verified yet** |
| SBI | WRITE | 4 | SBI write completes |
| UART | AWAIT_RX | 5 | Previously queued UART RX operation completes |

Opcode 6 (NOOP) remains available through the legacy controller.
The current VHDL bridge accepts only instance 1, and UART channel
selection remains fixed in VHDL. New VVC types, channels, instances,
variable-length payloads, and correlated asynchronous results require
further VHDL protocol design.

## Verification and acceptance

1. Existing `make regression` must continue to pass.
2. Additional `test_vvc_api` module must pass two cocotb tests.
3. Unsupported instances must be rejected without dispatching to VHDL.
4. Do not claim independent generic VVC dispatch until a second
   VHDL-backed VVC target/instance is demonstrated through the schema.

The API facade demonstrates reusable **Python call structure**, not
generalized VHDL routing or overall framework novelty.

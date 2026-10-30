# Generic Python–UVVM VVC API

## Objective

Extend the existing Python–UVVM framework to support
multiple VVC types without duplicating transport logic.

## Existing implementation

- CommandTransport handles command transfer and synchronization.
- UVVMController provides UART and SBI operations.
- uart_cosim_th.vhd decodes seven fixed command opcodes.
- VVC instance indices are currently hardcoded.

## Proposed command model

A generic command should identify:

1. Target VVC type
2. VVC instance
3. Operation
4. Command arguments
5. Completion semantics

## Design requirements

R1: Preserve existing UART and SBI functionality.
R2: Reuse the existing command transport where possible.
R3: Support configurable VVC targets and instances.
R4: Distinguish command acceptance from execution completion.
R5: Propagate verification failures to Python.
R6: Maintain backward compatibility with existing regression tests.

## Open design questions

- How should commands be encoded across the Python/VHDL boundary?
- How should variable-length arguments be handled?
- How should VVC-specific channels be represented?
- How should asynchronous results be associated with commands?
- Which VVC types are required to demonstrate reusability?

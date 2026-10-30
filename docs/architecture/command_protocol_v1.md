# Python–UVVM Command Protocol v1

Status: Design proposal — not implemented.

## Objective

Provide a reusable command interface between Python/cocotb
and multiple UVVM Verification Components (VVCs).

## Command interface

| Signal | Width | Description |
|---|---:|---|
| cmd_valid | 1 | Python presents a command |
| cmd_ready | 1 | Bridge initialization complete |
| cmd_vvc_type | 4 | Target VVC type |
| cmd_instance | 8 | Target VVC instance |
| cmd_operation | 8 | Requested VVC operation |
| cmd_addr | 16 | Address argument |
| cmd_data | 32 | Data argument |
| cmd_busy | 1 | Command being processed |
| cmd_done | 1 | Command response available |
| cmd_status | 2 | Command result |

## Initial VVC support

- SBI VVC, instance 1
- SBI VVC, instance 2

## Completion semantics

A command is held valid until the bridge acknowledges
completion through cmd_done.

For synchronous operations, cmd_done indicates that
the requested VVC operation has completed.

Asynchronous operations are outside the initial v1 scope.

## Result status

- 00: Success
- 01: Verification failure
- 10: Unsupported command or target
- 11: Internal protocol error

## Initial requirements

R1: Support two independently addressable SBI VVC instances.
R2: Preserve command ordering.
R3: Return a response for every accepted command.
R4: Detect unsupported targets and operations.
R5: Propagate UVVM verification failures.
R6: Preserve compatibility with the existing regression suite.

## Limitations

- Fixed-width command arguments.
- One outstanding Python command at a time.
- No variable-length payloads.
- No asynchronous result retrieval.
- No generic VVC support beyond the implemented adapters.

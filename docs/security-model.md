# Security Model

## Boundary

Wukong is a coordination contract, not a privilege escalation layer.

## Controls

- project-control gate before substantive work
- explicit authorization provenance in every task packet
- no recursion by default
- historian merge with CAS
- independent verification before completion
- fail-closed Product Design gate

## Exclusions

Public releases must not include:

- secrets or machine credentials
- private evidence logs
- private task dumps
- private project outputs
- live machine config


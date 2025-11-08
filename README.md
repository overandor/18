# Solana Liquidity Kernel

This repository contains the code for a dynamic, verifiable, Solana-native multi-pool router with CPI safety and off-chain deterministic path selection.

## Directory Layout

- `program/`: Bare Solana CPI router (Rust)
- `anchor/`: Anchor wrapper for program
- `registry/`: Dynamic pool registry
- `offchain/`: Deterministic orchestrator
- `executors/`: Python-based execution kernel
- `docs/`: Documentation and disclosure files
- `scripts/`: Deployment and provenance scripts
- `deployments/`: Deployment metadata
- `contracts/`: Solidity contracts
- `common/`: Common Python modules
- `zk/`: Zero-knowledge proof circuits
- `tests/`: Integration tests

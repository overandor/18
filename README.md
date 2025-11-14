# Solana Multi-Pool Swap Program

This program finds the most efficient swap path across various Solana liquidity pools and executes the trade using CPI.

## Overview

This is a bare-metal Solana program written in Rust. It takes a bundle of swap "legs" as input, verifies that each leg is part of a valid and sequential path, and then executes the swaps in a single atomic transaction. If any part of the swap fails, the entire transaction reverts, ensuring that there are no partial fills or loss of funds.

The core logic is contained entirely within the on-chain program, ensuring that all operations are verifiable and trustless. There are no off-chain components or external dependencies required for the program to function.

## How it Works

1.  **Input:** The program receives a `SwapBundle`, which is a serialized vector of `SwapLeg` structs. Each `SwapLeg` defines a single swap to be performed, including the pool to use, the input and output tokens, and the amount to swap.
2.  **Validation:** The program performs a series of on-chain checks to ensure the validity of the swap bundle. This includes verifying that the pools are whitelisted and that the legs form a continuous and valid path.
3.  **Execution:** The program uses Cross-Program Invocation (CPI) to call the swap instruction on each of the specified pools, in the order they are provided in the bundle.
4.  **Atomicity:** The entire bundle is executed within a single Solana transaction. This means that either all swaps succeed, or the entire transaction is reverted. This guarantees that the swap is atomic and that there is no risk of partial execution.

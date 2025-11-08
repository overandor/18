import fs from "fs";
import fetch from "node-fetch";
import { PublicKey } from "@solana/web3.js";
import { serialize } from "borsh";

class SwapLeg {
  constructor(
    public pool_program: Uint8Array,
    public pool_account: Uint8Array,
    public token_in: Uint8Array,
    public token_out: Uint8Array,
    public amount_in: bigint,
    public min_out: bigint
  ) {}
}

class SwapBundle {
  constructor(public legs: SwapLeg[]) {}
}

const schema = new Map([
  [SwapLeg, { kind: "struct", fields: [
    ["pool_program", [32]],
    ["pool_account", [32]],
    ["token_in", [32]],
    ["token_out", [32]],
    ["amount_in", "u64"],
    ["min_out", "u64"],
  ]}],
  [SwapBundle, { kind: "struct", fields: [["legs", [SwapLeg]]] }],
]);

async function buildRegistry() {
  const [raydium, orca, meteora] = await Promise.all([
    fetch("https://api.raydium.io/v2/sdk/liquidity/mainnet.json").then(r => r.json()),
    fetch("https://api.orca.so/allPools").then(r => r.json()),
    fetch("https://api.meteora.ag/pools").then(r => r.json())
  ]);
  const merged = [
    ...raydium.official,
    ...orca.pools,
    ...meteora.pools
  ].slice(0, 60);
  fs.writeFileSync("../registry/pools_registry.json", JSON.stringify(merged, null, 2));
}

export function buildBundleFromRegistry(registry, path) {
  const legs = path.map(p => new SwapLeg(
    new PublicKey(p.programId).toBytes(),
    new PublicKey(p.poolAccount).toBytes(),
    new PublicKey(p.tokenA).toBytes(),
    new PublicKey(p.tokenB).toBytes(),
    BigInt(1_000_000),
    BigInt(995_000)
  ));
  const bundle = new SwapBundle(legs);
  return Buffer.from(serialize(schema, bundle));
}

buildRegistry();

import { Connection, Keypair, Transaction, sendAndConfirmTransaction } from "@solana/web3.js";
import { buildBundleFromRegistry } from "./arb_builder.js";
import pools from "../../registry/pools_registry.json" assert { type: "json" };
import fs from "fs";

const keypair = Keypair.fromSecretKey(Uint8Array.from(JSON.parse(fs.readFileSync("./keypair.json", "utf8"))));
const conn = new Connection("https://api.mainnet-beta.solana.com", "confirmed");
const programId = new PublicKey(process.env.ROUTER_PROGRAM!);

const path = pools.slice(0, 3); // Example: 3-leg atomic path
const bundleData = buildBundleFromRegistry(pools, path);

const tx = new Transaction().add({
  programId,
  keys: path.flatMap(p => [
    { pubkey: new PublicKey(p.poolAccount), isSigner: false, isWritable: true },
    { pubkey: new PublicKey(p.tokenA), isSigner: false, isWritable: true },
    { pubkey: new PublicKey(p.tokenB), isSigner: false, isWritable: true }
  ]),
  data: bundleData,
});

await sendAndConfirmTransaction(conn, tx, [keypair]);
console.log("Atomic path executed.");

// Minimal Phantom (Solana) wallet helper. No wallet-adapter dependency.
import { VersionedTransaction } from '@solana/web3.js'

export function getProvider() {
  const p = (window.phantom && window.phantom.solana) || window.solana
  return p && p.isPhantom ? p : null
}

export async function connectWallet() {
  const p = getProvider()
  if (!p) throw new Error('Phantom not found — install the Phantom browser extension.')
  const res = await p.connect()
  return res.publicKey.toString()
}

function b64ToBytes(b64) {
  return Uint8Array.from(atob(b64), (c) => c.charCodeAt(0))
}

function bytesToB64(bytes) {
  let binary = ''
  const arr = new Uint8Array(bytes)
  for (let i = 0; i < arr.length; i++) binary += String.fromCharCode(arr[i])
  return btoa(binary)
}

// Deserialize an unsigned base64 versioned tx, sign it with Phantom (sign only,
// no broadcast), and return the signed tx as base64 for the backend to submit.
export async function signUnsignedTxB64(unsignedB64) {
  const p = getProvider()
  if (!p) throw new Error('Phantom not found')
  const tx = VersionedTransaction.deserialize(b64ToBytes(unsignedB64))
  const signed = await p.signTransaction(tx)
  return bytesToB64(signed.serialize())
}

# Bot Hot Wallet (opt-in, gated) — enabling guide

The bot hot wallet lets **unattended** bots place REAL Solana swaps by signing
server-side. It is **DISABLED by default** and ships deny-all. Treat enabling it
as handling real money.

## Safety model (enforced in `app/services/hotwallet_service.py`)
- No config row, or `enabled=False` → every trade refused.
- Token allowlist starts **EMPTY = deny-all**. A swap's OUTPUT mint must be
  explicitly allowlisted.
- Per-day USD cap (default **$10**) across all hot-wallet swaps.
- Secret key stored **Fernet-encrypted**; decrypted in-memory only at signing.

It is **not** wired into the live `/api/v1/bot/orders` path. Wiring + enabling is
a deliberate operator action.

## To enable (only with a throwaway, sparsely-funded wallet)

1. Generate an encryption key and set it as a Docker secret / env (NEVER commit):
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   # put into the environment as WALLET_ENC_KEY (compose env / docker secret)
   ```
2. Insert the encrypted secret key + config (example, inside the backend container):
   ```python
   from app.database import SessionLocal
   from app.models import BotHotWallet
   from app.services.hotwallet_service import encrypt_secret
   db = SessionLocal()
   db.add(BotHotWallet(
       pubkey="<wallet pubkey>",
       encrypted_secret=encrypt_secret("<base58-or-bytes secret>"),
       enabled=True,
       max_usd_per_day=10.0,
       token_allowlist=["<output mint you allow>"],  # empty = deny-all
   ))
   db.commit()
   ```
3. Fund the wallet with a tiny amount only. Verify caps/allowlist behave before
   trusting any bot.

Removing `WALLET_ENC_KEY` from the environment makes signing impossible (fail-safe).

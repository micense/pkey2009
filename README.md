# pkey2009

> [!IMPORTANT]
> Research/educational use only. These keys were not issued by Microsoft and
> will not activate against its servers. Don't use them to activate real
> products.

Oracle-free keygen for **PKEY2009**, the 25-character "N-style" key format
used across Microsoft's modern stack (Windows 10/11 and Server, Office, SQL
Server, Visual Studio, SharePoint, Exchange). Keys are computed arithmetically
— no `pidgenx.dll` calls, no network, no oracle.

**Key result:** the shared 10-bit checksum is plain **CRC-32** (poly
`0x04C11DB7`, init `0xFFFFFFFF`) over the 16-byte key block, truncated to
10 bits. Derive it once, mint any SKU.

## Quick start

`keygen/python/` is a [uv](https://docs.astral.sh/uv/) project; `uv run`
handles the environment.

```bash
cd keygen/python

uv run pkey2009 gen win11pro
uv run pkey2009 gen sql2025ent -n 5
uv run pkey2009 gen 5219 -S 0xDEADBEEF
uv run pkey2009 decode W269N-WFGWX-YVC9B-4J6C9-T83GX
uv run pkey2009 list --search Workstation
```

From the repo root, prefix with `--directory keygen/python`. `python -m
pkey2009` also works.

As a library:

```python
from pkey2009 import forge, load_masks

masks, _ = load_masks()
key, ck = forge(group=5219, serial=0, security=0xDEADBEEF, upgrade=1, masks=masks)
```

## Layout

| Path | Contents |
|---|---|
| `keygen/python/` | uv project: package, CLI, lockfile |
| `res/crc_full_masks.json` | 104-column GF(2) mask table + CRC-32 params |
| `res/sku_catalog.json` | SKU registry: group, edition, channel, part #, serials |
| `docs/` | [format](docs/pkey2009.md) · [usage](docs/usage.md) · [research](docs/research.md) |

## Scope

A key `pidgenx.dll` accepts is **format-valid**, not activated. KMS, retail,
and cloud activation are separate gates. See [usage](docs/usage.md).

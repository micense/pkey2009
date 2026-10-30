# pkey2009

> **Research/educational use only.** These keys were not issued by Microsoft and
> will not activate against its servers. Don't use them to activate real
> products.

Oracle-free keygen for **PKEY2009**, the 25-character "N-style" key format used
across Microsoft's modern stack (Windows 10/11 and Server, Office, SQL Server,
Visual Studio, SharePoint, Exchange). Keys are computed arithmetically — no
`pidgenx.dll` calls, no network, no oracle.

**Key result:** the shared 10-bit checksum is plain **CRC-32** (poly
`0x04C11DB7`, init `0xFFFFFFFF`) over the 16-byte key block, truncated to 10
bits. Derive it once, mint any SKU.

## Usage

```bash
uvx pkey2009 gen win11pro
uvx pkey2009 gen sql2025ent -n 5
uvx pkey2009 gen 5219 -S 0xDEADBEEF
uvx pkey2009 decode W269N-WFGWX-YVC9B-4J6C9-T83GX
uvx pkey2009 list --search Workstation
```

Or install it with `pip install pkey2009` (Python 3.11+); `python -m pkey2009`
also works.

As a library:

```python
from pkey2009 import forge, load_masks

masks, _ = load_masks()
key, ck = forge(group=5219, serial=0, security=0xDEADBEEF, upgrade=1, masks=masks)
```

## Scope

A key `pidgenx.dll` accepts is **format-valid**, not activated. KMS, retail, and
cloud activation are separate gates.

## Links

- [Project home](https://micense.github.io/pkey2009) — browser keygen and SKU catalog
- [Documentation](https://github.com/micense/pkey2009/wiki)
- [Source](https://github.com/micense/pkey2009)

Licensed under AGPL-3.0-or-later.

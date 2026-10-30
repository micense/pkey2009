# Usage

Run from `keygen/python/`, or add `--directory keygen/python` from the repo
root.

```
uv run pkey2009 gen    <alias|group> [-s serial] [-S security] [-u upgrade] [-n count] [--zero-security] [-v] [--json]
uv run pkey2009 decode <key> [--json]
uv run pkey2009 list   [product] [--channel C] [--search Q] [--edition E] [--limit N] [--all] [--collapse] [--json]
```

- `gen` — alias (`win11pro`, `sql2025ent`, …) or raw group ID. Random 53-bit
  `security` by default; serial/upgrade follow the SKU (SQL uses `upgrade=1`).
  `--json` for machine-readable output.
- `decode` — split a key and look up its group, flagging checksum mismatches.
- `list` — browse the catalog; narrow with `<product>`, `--search`, or
  `--channel`.

Numbers accept `0x`. `-h` shows all options.

## Common groups

| Group | Product |
|---:|---|
| 3311 | Windows 10/11 Pro |
| 3290 | Windows 10/11 Enterprise |
| 3918 | Windows 10/11 Pro Workstation |
| 4541 | Windows Server 2022 Standard |
| 4929 | Windows Server 2025 Standard |
| 4915 | Windows Server 2025 Datacenter |
| 5219 | SQL Server 2025 Enterprise |
| 5228 | SQL Server 2025 Standard |
| 5285 | Visual Studio 2026 Enterprise |
| 5295 | Visual Studio 2026 Professional |
| 4821 | Visual Studio 2022 Enterprise |

`list --all` prints the full registry. Each `pidgenx.dll` accepts only the
groups in its paired pkeyconfig, so a wrong-product key returns `0x8A010001`
("known group, wrong product"), not `0x8A010101` ("unknown group / bad
checksum").

## Format-valid vs. activation

| Gate | Forged key |
|---|---|
| `pidgenx.dll` format check | ✅ |
| Windows edition switch | ✅ |
| Offline Visual Studio activation | ✅ |
| SQL setup edition / `SERVERPROPERTY('Edition')` | ✅ |
| `slmgr /ipk` (same pidgenx) | likely ✅ |
| KMS activation | needs a KMS host — out of scope |
| Cloud / MAK activation | ❌ (never issued by Microsoft) |

Format validity is what setup checks. Activation is a separate problem.

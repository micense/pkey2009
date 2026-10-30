"""Generate PKEY2009 product keys for Microsoft's 2025-generation stack.

Covers most of the new Microsoft products. The keys pass format validation in each product's own
pidgenx.dll.

Examples::

    pkey2009 gen win11pro
    pkey2009 gen sql2025ent -n 5
    pkey2009 gen 3311 -S 0xDEADBEEF
    pkey2009 decode W269N-WFGWX-YVC9B-4J6C9-T83GX
    pkey2009 list windows --channel Retail --limit 20
    pkey2009 list --search Workstation
"""

import json
import re
import secrets
import sys
from pathlib import Path
from typing import Annotated  # at module scope so Typer can resolve the CLI annotations

DIGITS = "BCDFGHJKMPQRTVWXY2346789"
BASE_MAX = 24**25


def _data_dir() -> Path:
    """Find the ``res/`` data directory.

    This module sits in ``keygen/python/pkey2009/`` and the JSON lives in
    ``res/`` at the repository root. Walk upwards until ``res/`` turns up.
    """
    here = Path(__file__).resolve()
    for base in here.parents:
        candidate = base / "res"
        if (candidate / "crc_full_masks.json").exists():
            return candidate
    return Path("res").resolve()  # fall back to res/ in the working directory


DATA = _data_dir()

# Only the CLI needs typer and rich; library users importing encode, decode,
# forge, or load_masks don't have to install them. The CLI body is deferred so
# this module still imports cleanly in a bare Python environment.

# ───────────────────── key encoding ─────────────────────


def encode(group: int, serial: int, security: int, checksum: int, upgrade: int) -> str:
    n = (
        (group & 0xFFFFF)
        | ((serial & 0x3FFFFFFF) << 20)
        | ((security & ((1 << 53) - 1)) << 50)
        | ((checksum & 0x3FF) << 103)
        | ((upgrade & 1) << 113)
    )
    if n >= BASE_MAX:
        raise ValueError("tuple doesn't fit in 25 base-24 digits")
    digits = []
    for _ in range(25):
        digits.append(n % 24)
        n //= 24
    digits.reverse()
    s = "".join(DIGITS[d] for d in digits)
    pos = DIGITS.index(s[0])
    rest = s[1:]
    key = rest[:pos] + "N" + rest[pos:]
    return "-".join(key[i : i + 5] for i in range(0, 25, 5))


def decode(key: str) -> dict:
    k = key.upper().replace("-", "")
    if len(k) != 25 or "N" not in k:
        raise ValueError(f"not a PKEY2009-style key: {key!r}")
    pos = k.index("N")
    s = DIGITS[pos] + k.replace("N", "", 1)
    n = 0
    for c in s:
        if c not in DIGITS:
            raise ValueError(f"invalid digit {c!r} in {key!r}")
        n = n * 24 + DIGITS.index(c)
    n |= 1 << 114
    return {
        "group": n & 0xFFFFF,
        "serial": (n >> 20) & 0x3FFFFFFF,
        "security": (n >> 50) & ((1 << 53) - 1),
        "checksum": (n >> 103) & 0x3FF,
        "upgrade": (n >> 113) & 1,
    }


# ───────────────────── checksum via mask table ─────────────────────

_masks_cache = None
_const_cache = 0


def load_masks():
    global _masks_cache, _const_cache
    if _masks_cache is None:
        with open(DATA / "crc_full_masks.json") as f:
            d = json.load(f)
        _masks_cache = (d["masks"], set(d["determined"]))
        _const_cache = int(d.get("constant", 0))
    return _masks_cache


# PKEY2009's checksum is ordinary CRC-32: polynomial 0x04C11DB7, init
# 0xFFFFFFFF, MSB-first, standard final inversion. It runs over the 16-byte
# key block
#   block = (group | serial<<20 | security<<50 | upgrade<<113)  little-endian
# with the 10 checksum bits (103..112) cleared, and the result is cut to its
# low 10 bits:  ck = (~CRC32(block)) & 0x3FF.
#
# Because CRC-32 is GF(2)-linear, ck also equals CONSTANT XOR (masks[k] for
# every set input bit k), with CONSTANT = ck(0) and masks[] the 104-column
# table in res/crc_full_masks.json. This module uses that form.
# `product` is accepted for compatibility but never used.


def predict_checksum(
    group: int, serial: int, security: int, upgrade: int, masks=None, product: str | None = None
) -> int:
    if masks is None:
        masks, _ = load_masks()
    else:
        load_masks()  # ensure the constant is cached
    X = (
        (group & ((1 << 20) - 1))
        | ((serial & ((1 << 30) - 1)) << 20)
        | ((security & ((1 << 53) - 1)) << 50)
        | ((upgrade & 1) << 103)
    )
    ck = _const_cache
    for k in range(104):
        if (X >> k) & 1:
            ck ^= masks[k]
    return ck & 0x3FF


def forge(
    group: int,
    serial: int = 0,
    security: int = 0,
    upgrade: int = 0,
    masks=None,
    product: str | None = None,
):
    ck = predict_checksum(group, serial, security, upgrade, masks, product)
    return encode(group, serial, security, ck, upgrade), ck


def coverage_warning(group: int, serial: int, security: int, upgrade: int):
    # Every mask column is known, so the prediction is exact for any input.
    # Kept for API compatibility; this always returns None.
    _, det = load_masks()
    X = (
        (group & 0xFFFFF)
        | ((serial & 0x3FFFFFFF) << 20)
        | ((security & ((1 << 53) - 1)) << 50)
        | ((upgrade & 1) << 103)
    )
    bad = [k for k in range(104) if ((X >> k) & 1) and k not in det]
    if not bad:
        return None
    return f"input bits {bad} are set but undetermined in our mask table — predicted checksum may not pass PidGenX"


# ───────────────────── SKU catalog ─────────────────────

_catalog_cache = None


def load_catalog():
    global _catalog_cache
    if _catalog_cache is None:
        path = DATA / "sku_catalog.json"
        _catalog_cache = json.loads(path.read_text()) if path.exists() else []
    return _catalog_cache


SHORTCUTS = {
    "win11pro": ("windows", "Professional", "Volume:GVLK"),
    "win11pron": ("windows", "ProfessionalN", "Volume:GVLK"),
    "win11ent": ("windows", "Enterprise", "Volume:GVLK"),
    "win11entn": ("windows", "EnterpriseN", "Volume:GVLK"),
    "win11edu": ("windows", "Education", "Volume:GVLK"),
    "win11workstation": ("windows", "ProfessionalWorkstation", "Volume:GVLK"),
    "win11iot": ("windows", "IoTEnterpriseS", "Volume:GVLK"),
    "winsrv2022std": ("windows", "ServerStandard", None),
    "winsrv2022dc": ("windows", "ServerDatacenter", None),
    "winsrv2025std": ("windows", "ServerStandard", None),
    "winsrv2025dc": ("windows", "ServerDatacenter", None),
    "sql2025ent": ("sql2025", "Enterprise", "Volume:GVLK"),
    "sql2025entcore": ("sql2025", "Enterprise Core", "Volume:GVLK"),
    "sql2025std": ("sql2025", "Standard", "Volume:GVLK"),
    "sql2025web": ("sql2025", "Web", "Volume:GVLK"),
    "vs2026ent": ("vs2026", "Enterprise", "Retail"),
    "vs2026pro": ("vs2026", "Professional", "Retail"),
    # Older Visual Studio releases (same checksum, pre-VS2022 SKUs).
    "vs2022ent": ("vs2022", "Enterprise", "Retail"),
    "vs2022pro": ("vs2022", "Professional", "Retail"),
    "vs2019ent": ("vs2019", "Enterprise", "Retail"),
    "vs2019pro": ("vs2019", "Professional", "Retail"),
    "vs2017ent": ("vs2017", "Enterprise", "Retail"),
    "vs2017pro": ("vs2017", "Professional", "Retail"),
    "vs2017test": ("vs2017", "Test Professional", "Retail"),
    "ssms22": ("ssms22", "Enterprise", "Retail"),
    # Windows 8.1 SKUs.
    "win81pro": ("win81", "Professional", "Volume:GVLK"),
    "win81pron": ("win81", "ProfessionalN", "Volume:GVLK"),
    "win81ent": ("win81", "Enterprise", "Volume:GVLK"),
    "win81entn": ("win81", "EnterpriseN", "Volume:GVLK"),
    # Windows 8 SKUs.
    "win8pro": ("win8", "Professional", "Volume:GVLK"),
    "win8pron": ("win8", "ProfessionalN", "Volume:GVLK"),
    "win8ent": ("win8", "Enterprise", "Volume:GVLK"),
    "win8entn": ("win8", "EnterpriseN", "Volume:GVLK"),
    "win8core": ("win8", "Core", None),
}

# Office volume SKUs (2013–2024) from the catalog.
SHORTCUTS.update(
    {
        "office2024pp": ("office", "ProPlus2024Volume", "Volume:GVLK"),
        "office2021pp": ("office", "ProPlus2021Volume", "Volume:GVLK"),
        "office2021std": ("office", "Standard2021Volume", "Volume:GVLK"),
        "office2019pp": ("office", "ProPlus2019Volume", "Volume:GVLK"),
        "office2019std": ("office", "Standard2019Volume", "Volume:GVLK"),
        "office2016pp": ("office", "ProPlusVolume", "Volume:GVLK"),
        "office2016std": ("office", "StandardVolume", "Volume:GVLK"),
        # Office 2013 SKUs.
        "office2013pp": ("office2013", "ProPlusVolume", "Volume:GVLK"),
        "office2013std": ("office2013", "StandardVolume", "Volume:GVLK"),
        "office2013vispro": ("office2013", "VisioProVolume", "Volume:GVLK"),
        "office2013prjpro": ("office2013", "ProjectProVolume", "Volume:GVLK"),
    }
)
# Standalone Office apps (Visio, Project, Access, Outlook, Excel, PowerPoint,
# Publisher), Volume:GVLK/KMS-client editions.
SHORTCUTS.update(
    {
        "visio2024pro": ("office", "VisioPro2024Volume", "Volume:GVLK"),
        "visio2021pro": ("office", "VisioPro2021Volume", "Volume:GVLK"),
        "visio2021std": ("office", "VisioStd2021Volume", "Volume:GVLK"),
        "visio2019pro": ("office", "VisioPro2019Volume", "Volume:GVLK"),
        "visio2019std": ("office", "VisioStd2019Volume", "Volume:GVLK"),
        "project2024pro": ("office", "ProjectPro2024Volume", "Volume:GVLK"),
        "project2021pro": ("office", "ProjectPro2021Volume", "Volume:GVLK"),
        "project2021std": ("office", "ProjectStd2021Volume", "Volume:GVLK"),
        "project2019pro": ("office", "ProjectPro2019Volume", "Volume:GVLK"),
        "project2019std": ("office", "ProjectStd2019Volume", "Volume:GVLK"),
        "access2021": ("office", "Access2021Volume", "Volume:GVLK"),
        "access2019": ("office", "Access2019Volume", "Volume:GVLK"),
        "outlook2021": ("office", "Outlook2021Volume", "Volume:GVLK"),
        "outlook2019": ("office", "Outlook2019Volume", "Volume:GVLK"),
        "excel2021": ("office", "Excel2021Volume", "Volume:GVLK"),
        "excel2019": ("office", "Excel2019Volume", "Volume:GVLK"),
        "powerpoint2021": ("office", "PowerPoint2021Volume", "Volume:GVLK"),
        "powerpoint2019": ("office", "PowerPoint2019Volume", "Volume:GVLK"),
        "publisher2021": ("office", "Publisher2021Volume", "Volume:GVLK"),
        "publisher2019": ("office", "Publisher2019Volume", "Volume:GVLK"),
        # Office 2024 apps, Word standalone, and the Skype for Business client.
        "office2024std": ("office", "Standard2024Volume", "Volume:GVLK"),
        "access2024": ("office", "Access2024Volume", "Volume:GVLK"),
        "excel2024": ("office", "Excel2024Volume", "Volume:GVLK"),
        "outlook2024": ("office", "Outlook2024Volume", "Volume:GVLK"),
        "powerpoint2024": ("office", "PowerPoint2024Volume", "Volume:GVLK"),
        "word2024": ("office", "Word2024Volume", "Volume:GVLK"),
        "visio2024std": ("office", "VisioStd2024Volume", "Volume:GVLK"),
        "project2024std": ("office", "ProjectStd2024Volume", "Volume:GVLK"),
        "skypeforbusiness2024": ("office", "SkypeforBusiness2024Volume", "Volume:GVLK"),
        "skypeforbusiness2021": ("office", "SkypeforBusiness2021Volume", "Volume:GVLK"),
    }
)
# SQL Server 2016–2022 SKUs.
SHORTCUTS.update(
    {
        "sql2022ent": ("sql2022", "Enterprise", "Volume:GVLK"),
        "sql2022entcore": ("sql2022", "Enterprise Core", "Volume:GVLK"),
        "sql2022std": ("sql2022", "Standard", "Volume:GVLK"),
        "sql2022web": ("sql2022", "Web", "Volume:GVLK"),
        "sql2019ent": ("sql2019", "Enterprise", "Volume:GVLK"),
        "sql2019entcore": ("sql2019", "Enterprise Core", "Volume:GVLK"),
        "sql2019std": ("sql2019", "Standard", "Volume:GVLK"),
        "sql2019web": ("sql2019", "Web", "Volume:GVLK"),
        "sql2017ent": ("sql2017", "Enterprise", "Volume:GVLK"),
        "sql2017entcore": ("sql2017", "Enterprise Core", "Volume:GVLK"),
        "sql2017std": ("sql2017", "Standard", "Volume:GVLK"),
        "sql2017web": ("sql2017", "Web", "Volume:GVLK"),
        "sql2016ent": ("sql2016", "Enterprise", "Volume:GVLK"),
        "sql2016entcore": ("sql2016", "Enterprise Core", "Volume:GVLK"),
        "sql2016std": ("sql2016", "Standard", "Volume:GVLK"),
        "sql2016web": ("sql2016", "Web", "Volume:GVLK"),
    }
)
# Windows Server 2012–2025, plus SharePoint and Exchange.
SHORTCUTS.update(
    {
        "winsrv2022std": ("winserver2022", "ServerStandard", "Volume:GVLK"),
        "winsrv2022dc": ("winserver2022", "ServerDatacenter", "Volume:GVLK"),
        "winsrv2022azure": ("winserver2022", "ServerAzureCor", "Volume:GVLK"),
        "winsrv2022rdsh": ("winserver2022", "ServerRdsh", "Volume:GVLK"),
        "winsrv2016std": ("winserver2016", "ServerStandard", "Volume:GVLK"),
        "winsrv2016dc": ("winserver2016", "ServerDatacenter", "Volume:GVLK"),
        "winsrv2019std": ("winserver2019", "ServerStandard", "Volume:GVLK"),
        "winsrv2019dc": ("winserver2019", "ServerDatacenter", "Volume:GVLK"),
        "winsrv2025std": ("winserver2025", "ServerStandard", "Volume:GVLK"),
        "winsrv2025dc": ("winserver2025", "ServerDatacenter", "Volume:GVLK"),
        "winsrv2025azure": ("winserver2025", "ServerAzureCor", "Volume:GVLK"),
        "winsrv2012std": ("winserver2012", "ServerStandard", "Volume:GVLK"),
        "winsrv2012dc": ("winserver2012", "ServerDatacenter", "Volume:GVLK"),
        "winsrv2012r2std": ("winserver2012r2", "ServerStandard", "Volume:GVLK"),
        "winsrv2012r2dc": ("winserver2012r2", "ServerDatacenter", "Volume:GVLK"),
        "sharepoint2019": ("sharepoint2019", "MOSSPremiumNone", None),
        "sharepoint2019std": ("sharepoint2019", "MOSSNone", None),
        "sharepoint2019ent": ("sharepoint2019", "MOSSPremiumNone", None),
        "projectserver2019": ("sharepoint2019", "ProjectServerNone", None),
        "sharepoint2016": ("sharepoint2016", "MOSSPremiumNone", None),
        "sharepoint2016std": ("sharepoint2016", "MOSSNone", None),
        "sharepoint2016ent": ("sharepoint2016", "MOSSPremiumNone", None),
        "projectserver2016": ("sharepoint2016", "ProjectServerNone", None),
        "sharepoint2013": ("sharepoint2013", "MOSSPremiumNone", None),
        "sharepoint2013std": ("sharepoint2013", "MOSSNone", None),
        "sharepoint2013ent": ("sharepoint2013", "MOSSPremiumNone", None),
        "projectserver2013": ("sharepoint2013", "ProjectServerNone", None),
        "sharepointse": ("sharepointSE", "MOSSPremiumNone", None),
        "sharepointsestd": ("sharepointSE", "MOSSNone", None),
        "sharepointseent": ("sharepointSE", "MOSSPremiumNone", None),
        "projectserverse": ("sharepointSE", "ProjectServerNone", None),
        "exchange2019": ("exchange2019", "Enterprise", "Retail"),
        "exchange2019ent": ("exchange2019", "Enterprise", "Retail"),
        "exchange2019std": ("exchange2019", "Standard", "Retail"),
        "exchange2019hybrid": ("exchange2019", "Hybrid", "Retail"),
    }
)
CHANNEL_SUFFIXES = {
    "retail": "Retail",
    "gvlk": "Volume:GVLK",
    "mak": "Volume:MAK",
    "csvlk": "Volume:CSVLK",
    "oem": "OEM",
    "oemslp": "OEM:SLP",
    "oemdm": "OEM:DM",
    "oemnonslp": "OEM:NONSLP",
    "trial": "Trial",
    "eval": "Eval",
}


def resolve_alias(name: str) -> dict:
    catalog = load_catalog()
    norm = re.sub(r"[-_\s]", "", name.lower())
    base, override = norm, None
    for suf, ch in CHANNEL_SUFFIXES.items():
        if norm.endswith(suf) and norm != suf:
            base, override = norm[: -len(suf)], ch
            break
    if base in SHORTCUTS:
        product, edition, default_ch = SHORTCUTS[base]
        target = override or default_ch
        for sku in catalog:
            if sku["product"] != product:
                continue
            if edition and (sku["edition"] or "").lower() != edition.lower():
                continue
            if target is None or (sku["channel"] or "").startswith(target):
                return sku
        raise ValueError(f"alias {name!r}: no SKU matching {product}/{edition}/{target}")
    hits = [s for s in catalog if norm in re.sub(r"[-_\s]", "", (s.get("edition") or "").lower())]
    uniq_groups = set((s["product"], s["group"]) for s in hits)
    if len(uniq_groups) == 1:
        return hits[0]
    if hits:
        raise ValueError(
            f"alias {name!r} matches {len(uniq_groups)} distinct groups; use `list --search {name}` and pick a group ID"
        )
    raise ValueError(f"unknown alias {name!r} (try `list` to see available)")


# ───────────────────── CLI (typer + rich, from the uv project) ─────────────────────


def _cli_main():
    """Build and run the CLI.

    Typer and rich are imported inside this function, so importing the module
    from a plain environment never requires them.
    """
    import typer
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    console = Console()
    err_console = Console(stderr=True)

    def _channel_style(channel):
        if not channel:
            return "dim"
        if "GVLK" in channel:
            return "cyan"
        if "CSVLK" in channel:
            return "bright_cyan"
        if "MAK" in channel:
            return "blue"
        if "Retail" in channel:
            return "green"
        if "OEM" in channel:
            return "magenta"
        if "Trial" in channel or "Eval" in channel:
            return "yellow"
        return "white"

    def render_key(key: str):
        out = Text()
        for ch in key:
            if ch == "N":
                out.append(ch, style="bold yellow")
            elif ch == "-":
                out.append(ch, style="dim")
            else:
                out.append(ch, style="bold")
        return out

    app = typer.Typer(
        rich_markup_mode="rich",
        no_args_is_help=True,
        help="[bold]PKEY2009 keygen[/bold] for Microsoft's 2025-generation stack.\n\n"
        "Checksums derived by GF(2) linearity — no pidgenx call, pure XOR math.",
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    @app.command("gen")
    def cmd_gen(
        target: Annotated[
            str, typer.Argument(help="product alias (e.g. [cyan]win11pro[/]) or raw group ID")
        ],
        serial: Annotated[
            int | None,
            typer.Option(
                "-s",
                "--serial",
                help="serial field (default: SKU's first allocated serial, else 0)",
                parser=lambda x: int(x, 0),
            ),
        ] = None,
        security: Annotated[
            int | None,
            typer.Option(
                "-S",
                "--security",
                help="security field (default: random 53-bit)",
                parser=lambda x: int(x, 0),
            ),
        ] = None,
        upgrade: Annotated[
            int | None, typer.Option("-u", "--upgrade", help="upgrade bit (default: SKU-dependent)")
        ] = None,
        count: Annotated[int, typer.Option("-n", "--count", min=1, max=10000)] = 1,
        zero_security: Annotated[
            bool, typer.Option("--zero-security", help="use security=0 instead of random")
        ] = False,
        as_json: Annotated[bool, typer.Option("--json")] = False,
        verbose: Annotated[bool, typer.Option("-v", "--verbose")] = False,
    ):
        """Generate one or more keys for an alias or group ID."""
        masks, _ = load_masks()
        catalog = load_catalog()

        if target.isdigit() or target.lower().startswith("0x"):
            group = int(target, 0)
            sku = next((s for s in catalog if s["group"] == group), None)
        else:
            sku = resolve_alias(target)
            group = sku["group"]

        serial_val = serial if serial is not None else (sku.get("serial_start") or 0 if sku else 0)
        if upgrade is not None:
            upgrade_val = upgrade
        elif sku and sku["product"].startswith("sql"):
            upgrade_val = 1
        else:
            upgrade_val = 0

        warn = coverage_warning(group, serial_val, security or 0, upgrade_val)
        if warn:
            err_console.print(f"[yellow]⚠  warning:[/] {warn}")

        rows = []
        for _ in range(count):
            sec = security
            if sec is None:
                sec = 0 if zero_security else secrets.randbits(53)
            key, ck = forge(
                group, serial_val, sec, upgrade_val, masks, product=sku["product"] if sku else None
            )
            rows.append(
                {
                    "key": key,
                    "group": group,
                    "serial": serial_val,
                    "security": sec,
                    "upgrade": upgrade_val,
                    "checksum": ck,
                    "sku": sku,
                }
            )

        if as_json:
            for r in rows:
                r["security"] = f"0x{r['security']:X}"
                r["checksum"] = f"0x{r['checksum']:03X}"
                sku_r = r.pop("sku")
                r["edition"] = sku_r["edition"] if sku_r else None
                r["channel"] = sku_r["channel"] if sku_r else None
                r["product"] = sku_r["product"] if sku_r else None
                r["part_number"] = sku_r["part_number"] if sku_r else None
            console.print_json(data=rows)
            return

        for r in rows:
            console.print(render_key(r["key"]))
            if verbose:
                sku_r = r["sku"]
                console.print(
                    f"  [dim]group=[/]{r['group']}  "
                    f"[dim]serial=[/]{r['serial']}  "
                    f"[dim]security=[/]0x{r['security']:X}  "
                    f"[dim]upgrade=[/]{r['upgrade']}  "
                    f"[dim]ck=[/]0x{r['checksum']:03X}"
                )
                if sku_r:
                    ch = sku_r.get("channel") or ""
                    console.print(
                        f"  [dim]edition=[/]{sku_r.get('edition')}  "
                        f"[dim]channel=[/][{_channel_style(ch)}]{ch}[/]  "
                        f"[dim]part=[/]{sku_r.get('part_number')}  "
                        f"[dim]product=[/]{sku_r.get('product')}"
                    )

    @app.command("decode")
    def cmd_decode(
        key: Annotated[
            str, typer.Argument(help="25-character PKEY2009 key (with or without hyphens)")
        ],
        as_json: Annotated[bool, typer.Option("--json")] = False,
    ):
        """Split a key into its fields and look up its group in the catalog."""
        fields = decode(key)
        catalog = load_catalog()
        sku = next((s for s in catalog if s["group"] == fields["group"]), None)
        masks, _ = load_masks()
        predicted = predict_checksum(
            fields["group"], fields["serial"], fields["security"], fields["upgrade"], masks
        )
        matches = predicted == fields["checksum"]

        if as_json:
            console.print_json(
                data={
                    **fields,
                    "security_hex": f"0x{fields['security']:X}",
                    "checksum_hex": f"0x{fields['checksum']:03X}",
                    "predicted_checksum": f"0x{predicted:03X}",
                    "checksum_matches_mask_table": matches,
                    "sku": sku,
                }
            )
            return

        channel = (sku or {}).get("channel") or ""
        tbl = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
        tbl.add_column(style="dim", width=20)
        tbl.add_column()
        tbl.add_row("key", render_key(key.upper()))
        tbl.add_row(
            "group",
            f"{fields['group']}"
            + (
                f"  [bold]({sku['product']} · {sku['edition']})[/]"
                if sku
                else "  [red](unknown)[/]"
            ),
        )
        tbl.add_row("serial", f"{fields['serial']}")
        tbl.add_row("security", f"0x{fields['security']:014X}")
        tbl.add_row("upgrade", f"{fields['upgrade']}")
        tbl.add_row(
            "checksum",
            f"0x{fields['checksum']:03X}  [{'green' if matches else 'red'}]"
            + ("✓ matches mask table" if matches else f"✗ expected 0x{predicted:03X}")
            + "[/]",
        )
        if sku:
            tbl.add_row("channel", Text(channel, style=_channel_style(channel)))
            if sku.get("part_number"):
                tbl.add_row("part number", sku["part_number"])
            if sku.get("description"):
                tbl.add_row("description", sku["description"])
        console.print(Panel(tbl, title="[bold]PKEY2009[/]", border_style="cyan", width=100))

    @app.command("list")
    def cmd_list(
        product: Annotated[
            str | None, typer.Argument(help="filter by product or edition substring")
        ] = None,
        channel: Annotated[
            str | None,
            typer.Option("--channel", "-c", help="filter by channel (Retail, GVLK, MAK, OEM, …)"),
        ] = None,
        search: Annotated[
            str | None, typer.Option("--search", "-s", help="free-text search across every field")
        ] = None,
        edition: Annotated[
            str | None,
            typer.Option("--edition", "-e", help="filter by exact edition name (case-insensitive)"),
        ] = None,
        limit: Annotated[int, typer.Option("--limit", "-l", help="max rows to show")] = 60,
        all: Annotated[bool, typer.Option("--all", "-a", help="show every row (no limit)")] = False,
        collapse: Annotated[
            bool,
            typer.Option(
                "--collapse",
                help="one row per unique (group, edition, channel), hiding part-number variants",
            ),
        ] = False,
        as_json: Annotated[bool, typer.Option("--json")] = False,
    ):
        """Search and list SKUs from the catalog."""
        rows = load_catalog()
        if product:
            p = product.lower()
            rows = [
                s
                for s in rows
                if (s.get("product") or "").lower() == p or p in (s.get("edition") or "").lower()
            ]
        if edition:
            e = edition.lower()
            rows = [s for s in rows if e == (s.get("edition") or "").lower()]
        if channel:
            c = channel.lower()
            rows = [s for s in rows if c in (s.get("channel") or "").lower()]
        if search:
            q = search.lower()
            rows = [s for s in rows if q in json.dumps(s).lower()]
        if collapse:
            seen = {}
            for s in rows:
                k = (s["product"], s["group"], s["edition"], s["channel"])
                if k not in seen:
                    seen[k] = s
            rows = sorted(seen.values(), key=lambda s: (s["product"], s["group"]))

        total = len(rows)
        shown = rows if all else rows[:limit]

        if as_json:
            console.print_json(data=shown)
            return

        tbl = Table(
            box=box.SIMPLE_HEAVY,
            header_style="bold magenta",
            title=f"[bold]SKU catalog[/]  — showing {len(shown):,} of {total:,} rows"
            + ("  [dim](use --all for everything)[/]" if not all and total > limit else ""),
        )
        tbl.add_column("product", style="dim")
        tbl.add_column("group", justify="right", style="cyan")
        tbl.add_column("edition")
        tbl.add_column("channel")
        tbl.add_column("part")
        tbl.add_column("serials", style="dim")
        for s in shown:
            ch = s.get("channel") or ""
            serials = ""
            if s.get("serial_start") is not None and s.get("serial_end") is not None:
                a, b = s["serial_start"], s["serial_end"]
                serials = (
                    f"{a:,}"
                    if a == b
                    else f"{a:,}..{b:,}"
                    if b < 1_000_000
                    else f"{a:,}..{b / 1e6:.0f}M"
                )
            tbl.add_row(
                s.get("product") or "?",
                str(s.get("group")) if s.get("group") is not None else "?",
                s.get("edition") or "?",
                Text(ch, style=_channel_style(ch)),
                s.get("part_number") or "",
                serials,
            )
        console.print(tbl)
        if not all and total > limit:
            console.print(
                f"[dim]…{total - limit:,} more rows[/]  — pass [cyan]--all[/] to show, or narrow with [cyan]--channel[/] / [cyan]--search[/]"
            )

    # Report ValueError as a clean error instead of a traceback.
    try:
        app()
    except ValueError as e:
        err_console.print(f"[red]error:[/] {e}")
        sys.exit(2)


if __name__ == "__main__":
    _cli_main()

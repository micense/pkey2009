# Research notes

1. **Format.** Decoding real keys gave the 114-bit layout; only the 10-bit
   checksum gates well-formedness.

2. **Linearity.** Over GF(2), each input bit flips a fixed set of checksum
   bits, so the checksum is a constant XOR a 104-column mask table. Single-bit
   key pairs fed to pidgenx recovered all 104 columns.

3. **Function.** DEP+VEH single-step tracing of pidgenx's self-decrypting
   checksum blob (non-executable decryption slots fault on each decrypted
   instruction) exposed a byte-wise CRC-32 loop with `table[1] = 0x04C11DB7`.
   So the checksum is plain CRC-32 (init `0xFFFFFFFF`), low 10 bits — no
   per-group or per-era special cases.

4. **Proof.** Freshly minted keys return `HRESULT=0` from each product's own
   pidgenx, with the right edition/channel: Windows 8→11, Server 2012→2025,
   Office/SharePoint/Exchange, SQL 2016+, VS 2015+. A forged SQL key also
   completed an edition upgrade on a live instance.

**Scope.** SPP/OSPP core-platform products only. PKEY2005 lines (SQL 2014,
Exchange 2013/2016) and CAL/contractual licensing (BizTalk, MIM, TFS/Azure
DevOps Server, …) are out of scope.

/**
 * Curated SKUs for the web keygen, grouped by family. Groups and upgrade
 * conventions mirror the Python catalog (res/sku_catalog.json); the CLI
 * (`uv run pkey2009 list`) exposes the full set.
 */
export const SKUS = [
  // Windows client
  { name: 'Windows 10/11 Pro', group: 3311, upgrade: 0, family: 'Windows' },
  { name: 'Windows 10/11 Pro N', group: 3319, upgrade: 0, family: 'Windows' },
  { name: 'Windows 10/11 Enterprise', group: 3290, upgrade: 0, family: 'Windows' },
  { name: 'Windows 10/11 Education', group: 3281, upgrade: 0, family: 'Windows' },
  { name: 'Windows 10/11 Pro Workstation', group: 3918, upgrade: 0, family: 'Windows' },

  // Windows Server
  { name: 'Windows Server 2012 Standard', group: 1843, upgrade: 0, family: 'Windows Server' },
  { name: 'Windows Server 2012 Datacenter', group: 1849, upgrade: 0, family: 'Windows Server' },
  { name: 'Windows Server 2012 R2 Standard', group: 2527, upgrade: 0, family: 'Windows Server' },
  { name: 'Windows Server 2012 R2 Datacenter', group: 2535, upgrade: 0, family: 'Windows Server' },
  { name: 'Windows Server 2016 Standard', group: 3776, upgrade: 0, family: 'Windows Server' },
  { name: 'Windows Server 2016 Datacenter', group: 3764, upgrade: 0, family: 'Windows Server' },
  { name: 'Windows Server 2019 Standard', group: 4297, upgrade: 0, family: 'Windows Server' },
  { name: 'Windows Server 2019 Datacenter', group: 4300, upgrade: 0, family: 'Windows Server' },
  { name: 'Windows Server 2022 Standard', group: 4541, upgrade: 0, family: 'Windows Server' },
  { name: 'Windows Server 2022 Datacenter', group: 4546, upgrade: 0, family: 'Windows Server' },
  { name: 'Windows Server 2025 Standard', group: 4929, upgrade: 0, family: 'Windows Server' },
  { name: 'Windows Server 2025 Datacenter', group: 4915, upgrade: 0, family: 'Windows Server' },

  // SQL Server
  { name: 'SQL Server 2025 Enterprise', group: 5219, upgrade: 1, family: 'SQL Server' },
  { name: 'SQL Server 2025 Enterprise Core', group: 5221, upgrade: 1, family: 'SQL Server' },
  { name: 'SQL Server 2025 Standard', group: 5228, upgrade: 1, family: 'SQL Server' },

  // Visual Studio
  { name: 'Visual Studio 2026 Enterprise', group: 5285, upgrade: 0, family: 'Visual Studio' },
  { name: 'Visual Studio 2026 Professional', group: 5295, upgrade: 0, family: 'Visual Studio' },
  { name: 'Visual Studio 2022 Enterprise', group: 4821, upgrade: 0, family: 'Visual Studio' },
  { name: 'Visual Studio 2022 Professional', group: 4830, upgrade: 0, family: 'Visual Studio' },
  { name: 'Visual Studio 2019 Enterprise', group: 4339, upgrade: 0, family: 'Visual Studio' },
  { name: 'Visual Studio 2019 Professional', group: 4352, upgrade: 0, family: 'Visual Studio' },
  { name: 'Visual Studio 2017 Enterprise', group: 3699, upgrade: 0, family: 'Visual Studio' },
  { name: 'Visual Studio 2017 Professional', group: 3701, upgrade: 0, family: 'Visual Studio' },
];

/** SKUs grouped into {family, items} blocks, in first-seen family order. */
export const SKU_GROUPS = SKUS.reduce((groups, sku) => {
  let group = groups.find((entry) => entry.family === sku.family);
  if (!group) {
    group = { family: sku.family, items: [] };
    groups.push(group);
  }
  group.items.push(sku);
  return groups;
}, []);

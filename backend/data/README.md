# Data Directory

This directory contains the CSV data files that power the Carbon Scenario Explorer.

## Files

### `alloy_carbon_intensity.csv`
Material carbon intensity lookup table. Columns are material names, rows are recycled content levels (0%, 25%, 30%, 50%, 75%, 100%). Values are in kg CO2e/kg.

### `supporting_data.csv`
Manufacturing process parameters: grid intensities (kg CO2e/kWh), process energy values (kW, kWh/strike, etc.), physical constants (specific heat, efficiency), and utilization factors.

### `pmf/` directory
Product Material Footprint CSV files. Each file represents one product with component-level material breakdowns.

**Expected PMF schema:**
```
program, proxyProject, proxyConfig, name, component, subcomponent,
materialCategory, materialName, substanceGroup, substanceName,
productGroup, productLine, status,
massMobilizedBioCert, massMobilizedPrimary, massMobilizedRcCert, massMobilizedRen,
massShippedBioCert, massShippedPrimary, massShippedRcCert, massShippedRen,
materialMassShipped, materialMassMobilized, date, lastUpdated
```

A simplified 6-column mass variant is also supported (without bio/ren columns).

### `footprint/` directory
Reference product footprint data with GHG and materials breakdowns per component.

### `saved_scenarios.json`
Runtime scenario persistence (auto-generated, gitignored).

## Bringing Your Own Data

1. Place PMF CSV files in `pmf/` following the schema above
2. Update `alloy_carbon_intensity.csv` with your material library
3. Update `supporting_data.csv` with your process parameters
4. Restart the backend — data is loaded at startup

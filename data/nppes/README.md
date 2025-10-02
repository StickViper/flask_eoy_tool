# NPPES Data

This folder contains NPPES (National Plan and Provider Enumeration System) bulk data downloads.

## Structure

```
nppes/
└── PCP Hunt/
    └── NPPES_Data_Dissemination_September_2025_V2/
        ├── nppes_filter_pcps.py         # v3.0 Filter script
        ├── npidata_pfile_*.csv          # Raw NPPES data (LARGE - gitignored)
        ├── FILTERED_pcps_TX_*.csv       # Filtered output (gitignored)
        ├── FILTERED_pcps_TN_*.csv
        ├── FILTERED_pcps_OK_*.csv
        └── FILTERED_pcps_OR_*.csv
```

## Python Filter Script

Location: `PCP Hunt/NPPES_Data_Dissemination_September_2025_V2/nppes_filter_pcps.py`

**Run from that directory:**
```bash
cd "PCP Hunt/NPPES_Data_Dissemination_September_2025_V2"
python3 nppes_filter_pcps.py
```

## Download NPPES Data

1. Go to: https://download.cms.gov/nppes/NPI_Files.html
2. Download "NPPES Data Dissemination" (monthly update)
3. Extract to this folder
4. Run filter script

## Note

All `.csv` files are gitignored (too large). Only the Python script is tracked in git.

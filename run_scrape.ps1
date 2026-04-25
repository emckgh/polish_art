# Run the weekly scraper — call from project root
# Usage: .\run_scrape.ps1 [--force] [--seed]
param(
    [switch]$Force,
    [switch]$Seed
)

$args_list = @()
if ($Force) { $args_list += "--force" }
if ($Seed)  { $args_list += "--seed" }

& "$PSScriptRoot\.venv\Scripts\python.exe" -m src.scripts.run_weekly_scrape @args_list

<!--
---
weight: 302
title: "Running Scripts"
description: "Running PyneCore scripts from the command line"
icon: "play_circle"
date: "2025-03-31"
lastmod: "2025-07-24"
draft: false
toc: true
categories: ["Usage", "CLI", "Scripting"]
tags: ["run", "scripts", "execution", "backtesting", "command-line"]
---
-->

# Running Scripts

The `run` command is used to execute PyneCore scripts with historical OHLCV data. This page covers the details of how to use this command effectively.

## Basic Usage

The basic syntax for running a script is:

```bash
pyne run SCRIPT DATA [OPTIONS]
```

Where:
- `SCRIPT`: Path to the PyneCore script (.py) file
- `DATA`: Path to the OHLCV data (.ohlcv) file
- `OPTIONS`: Additional options to customize the execution

## Simple Example

```bash
# Run a script using paths within the working directory
pyne run my_strategy.py eurusd_data.ohlcv
```

This command will:
1. Look for `my_strategy.py` in the `workdir/scripts/` directory
2. Look for `eurusd_data.ohlcv` in the `workdir/data/` directory
3. Execute the script with the provided data
4. Save outputs to the `workdir/output/` directory

## Command Arguments

The `run` command has two required arguments:

- `SCRIPT`: The script file to run. If only a filename is provided, it will be searched in the `workdir/scripts/` directory.
- `DATA`: The OHLCV data file to use. If only a filename is provided, it will be searched in the `workdir/data/` directory.

<small>
Note: you don't need to write the `.py` and `.ohlcv` extensions in the command.
</small>

## Command Options

The `run` command supports several options to customize the execution:

### Date Range Options

- `--from`, `-f`: Start date (UTC) in 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS' format. If not specified, it will use the first date in the data
- `--to`, `-t`: End date (UTC) in 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS' format. If not specified, it will use the last date in the data.

Example:
```bash
# Run a script for a specific date range
pyne run my_strategy.py eurusd_data.ohlcv --from "2023-01-01" --to "2023-12-31"
```

### Output Path Options

- `--plot`, `-pp`: Path to save the plot data (CSV format). If not specified, it will be saved as `<script_name>.csv` in the `workdir/output/` directory.
- `--strat`, `-sp`: Path to save the strategy statistics (CSV format). If not specified, it will be saved as `<script_name>_strat.csv` in the `workdir/output/` directory.
- `--trade`, `-tp`: Path to save the trade data (CSV format). If not specified, it will be saved as `<script_name>_trade.csv` in the `workdir/output/` directory.

Example:
```bash
# Specify custom output paths
pyne run my_strategy.py eurusd_data.ohlcv --plot custom_plot.csv --strat custom_stats.csv --trade custom_trades.csv
```

## Symbol Information

When running a script, PyneCore needs symbol information to provide the script with details about the financial instrument being analyzed. This information is stored in a TOML file with the same name as the OHLCV file but with a `.toml` extension.

For example, if your data file is `eurusd_data.ohlcv`, the system will look for symbol information in `eurusd_data.toml`.

The symbol information file should be located in the same directory as the OHLCV file and contain information like:
- Symbol name and description
- Exchange information
- Currency
- Session times
- Tick size and value
- etc.

More details about the symbol information [can be found here](../overview/configuration.md#symbol-configuration).

If the symbol information file is not found, the command will display an error.

## Progress Tracking

When running a script, the PyneCore CLI shows a progress bar with:
- Current date being processed
- Elapsed time
- Estimated remaining time
- Visual progress indicator

Example:
```
✓ Running script... [██████████████████████████████] 2023-12-31 12:30:00 / 0:01:45
```

## Output Files

After the script execution completes, several output files are created:

### Plot Data (CSV)

Contains the values plotted by the script for each bar. This includes all values passed to `plot()` functions in your script.

**Default filename**: `<script_name>.csv`

### Strategy Statistics (CSV)

If your script is a strategy, this file contains comprehensive TradingView-compatible statistics about the trading performance, including:
- **Overview metrics**: Net profit, gross profit/loss, max equity runup/drawdown, buy & hold return
- **Performance ratios**: Sharpe ratio, Sortino ratio, profit factor
- **Trade statistics**: Total/winning/losing trades, percent profitable, average trade metrics
- **Position analysis**: Largest winning/losing trades, average bars in trades
- **Long/Short breakdown**: Separate statistics for long and short positions
- **Risk metrics**: Max contracts held, commission paid, margin calls

**Default filename**: `<script_name>_strat.csv`

### Trade Data (CSV)

If your script is a strategy, this file contains detailed trade-by-trade data with entry and exit records:
- **Trade information**: Trade number, bar index, entry/exit type, signal ID
- **Timing data**: Date/time of entry and exit
- **Price data**: Entry/exit prices in the symbol's currency
- **Position data**: Number of contracts traded
- **Performance metrics**: Profit/loss in currency and percentage
- **Cumulative tracking**: Running totals of profit and profit percentage
- **Risk analysis**: Maximum run-up and drawdown for each trade

**Default filename**: `<script_name>_trade.csv`

**Note**: This file exports individual trade records (entry/exit pairs), not the equity curve. The equity curve is tracked internally for statistics calculation.

## Examples

### Basic Usage

```bash
# Run a script with default options
pyne run my_strategy.py eurusd_data.ohlcv
```

### Specifying Date Range

```bash
# Run a script for a specific month
pyne run my_strategy.py eurusd_data.ohlcv --from "2023-03-01" --to "2023-03-31"
```

### Custom Output Paths

```bash
# Save outputs to custom locations
pyne run my_strategy.py eurusd_data.ohlcv \
  --plot ./analysis/my_plot.csv \
  --strat ./analysis/my_stats.csv \
  --trade ./analysis/my_trades.csv
```

## Troubleshooting

### Script File Not Found

```
Script file 'my_strategy.py' not found!
```

This error occurs when the script file cannot be found. Make sure:
- The file exists in the specified location
- If you provided just a filename, check that it exists in the `workdir/scripts/` directory
- The filename is spelled correctly (case sensitive)

### Data File Not Found

```
Data file 'eurusd_data.ohlcv' not found!
```

This error occurs when the data file cannot be found. Make sure:
- The file exists in the specified location
- If you provided just a filename, check that it exists in the `workdir/data/` directory
- The filename is spelled correctly (case sensitive)

### Symbol Info File Not Found

```
Symbol info file 'eurusd_data.toml' not found!
```

This error occurs when the symbol information file cannot be found. Make sure:
- The file exists in the same directory as the OHLCV file
- The filename matches the OHLCV file (with a `.toml` extension)
- If you're using a data provider, check that you've downloaded the symbol information
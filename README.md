## Readme file for trade-war-redux-2025 

This readme outlines calculations that go into tracking the US tariff actions. 

The ``.csv'' files discussed below will retain their naming conventions so they can be linked to directly for users purposes.

1. The file [tariff-summary.ipynb](tariff-summary.ipynb) and then plots the cross-country tariff graphic. **Note** that in that graphic, the change in the tariff is plotted. Not the estimated level. To get the level, simply add the 2024 tariff rate plust the estimated 2025 increase. 

The underlying data file is [tariff-summary-latest-data.csv](tariff-summary-latest-data.csv) for the current tariff rates (and other variables) for the top 50 trading partners of the U.S. 

The graphic plotting the long time series of applied tariffs uses the data set [federal-tax-duty.csv](federal-tax-duty.csv).

2. The file [tariff-summary-time.ipynb](tariff-summary-time.ipynb) constucts the aggregate, daily tariff rate. This starts from the base applied tariff rate for 2024 and estimates how the U.S. tariff rate has changed over time. 

The underlying data file produced is [daily-tariff-latest-data.csv](daily-tariff-latest-data.csv) and is then filled in the [tariff-summary.ipynb](tariff-summary.ipynb) notebook above.


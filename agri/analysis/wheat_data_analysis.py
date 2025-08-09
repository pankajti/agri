import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

# Clean data: focus on records with valid month and type (ending stocks)

wheat_df = pd.read_csv('../wheat_all_data.csv')
df = wheat_df.copy()
df = df[df['type'].notnull()]
df = df[df['month'].notnull()]

# Identify final actuals (month is NaN or contains 'data')
final_df = wheat_df[wheat_df['month'].isna() | (wheat_df['month'].str.lower() == 'data')]
final_stocks = final_df[['year', 'type']].rename(columns={'type': 'final_stocks'})

# Merge final estimates into forecast table
merged = df.merge(final_stocks, on='year', how='left')

# Calculate forecast error
merged['forecast_error'] = merged['type'] - merged['final_stocks']
merged['abs_error'] = np.abs(merged['forecast_error'])

# Compute bias and MAE by month
monthly_stats = merged.groupby('month').agg(
    mean_error=('forecast_error', 'mean'),
    mean_abs_error=('abs_error', 'mean'),
    count=('forecast_error', 'count')
).reset_index()


# Plotting: Forecast error distribution by month
plt.figure(figsize=(12, 6))
sns.boxplot(data=merged, x='month', y='forecast_error', order=sorted(merged['month'].unique()))
plt.axhline(0, color='red', linestyle='--')
plt.title('Forecast Error of Ending Stocks by Month (Forecast - Final)')
plt.ylabel('Forecast Error (Million Tons)')
plt.xlabel('Month')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

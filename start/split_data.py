import pandas as pd
import os

df_average = pd.read_csv('D:/github/statcan-food-prices/datasets/avg/18100245.csv')
df_provience = pd.read_csv('D:/github/statcan-food-prices/datasets/provience-wise/18100004.csv')

# Function to split the data according to each year from 2017 to 2026
def split_data_by_year(df_average, df_provience, start_year = 2017, end_year= 2026):
    avg_by_year = {}
    cpi_by_year = {}

    avg_count = 0
    cpi_count = 0
    
    for year in range(start_year, end_year + 1):
        avg_by_year[year] = df_average[
            df_average['REF_DATE'].str.startswith(str(year))
        ].copy()
        cpi_by_year[year] = df_provience[
            df_provience['REF_DATE'].str.startswith(str(year))
        ].copy()

        avg_count = avg_count + len(avg_by_year[year])
        cpi_count = cpi_count + len(cpi_by_year[year])

        print(f"\nYear: {year}")
        print("Average Shape: ", avg_by_year[year].shape)
        print("CPI Shape: ", cpi_by_year[year].shape)
    
    print(f"Avg Total Count: {avg_count}")
    print(f"Original Avg Count: {len(df_average)}")
    print(f"CPI Total Count: {cpi_count}")
    print(f"Original CPI Count: {len(df_provience)}")

    return avg_by_year, cpi_by_year

avg_by_year, cpi_by_year = split_data_by_year(
    df_average,
    df_provience,
)

# Function to save the split data into different CSV files.
def save_yearly_data(avg_by_year, cpi_by_year):
    avg_path = "D:/github/statcan-food-prices/data/loading/average-price"
    cpi_path = "D:/github/statcan-food-prices/data/loading/province-wise"

    os.makedirs(avg_path, exist_ok=True)
    os.makedirs(cpi_path, exist_ok=True)

    for year in avg_by_year:
        avg_by_year[year].to_csv(
            f"{avg_path}/average-price_{year}.csv",
            index = False
        )
        cpi_by_year[year].to_csv(
            f"{cpi_path}/provience-price_{year}.csv",
            index = False
        )
        print(f"Saved data for {year}")

save_yearly_data(
    avg_by_year,
    cpi_by_year
)
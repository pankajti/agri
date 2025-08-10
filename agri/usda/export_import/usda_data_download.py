from agri.database.connections import engine
import requests
import pandas as pd
import os
from agri.config.config import load_env

load_env()
usda_api_key= os.environ['usda_api_key']
def download_api_data(api_url):
    try:
        resp = requests.get(api_url)
        print(f"response for {api_url}" , resp.status_code)
        commodities_esr_df = pd.DataFrame(resp.json())
        return commodities_esr_df
    except Exception as e:
        print(str(e), api_url)
        return pd.DataFrame()


wsda_urls  = {'weekly_export_sales' : 'https://api.fas.usda.gov/api/esr/exports/commodityCode/{}/allCountries/marketYear/{}?api_key={}',
              'commodities':f'https://api.fas.usda.gov/api/esr/commodities?api_key={usda_api_key}',
              'countries':f'https://api.fas.usda.gov/api/esr/countries?api_key={usda_api_key}'}

def main():
    data = download_onetime_data()

    #print(data)
    all_export_import_data = []
    for i in range(1999 , 2026):
        for commodity in [1404,1301]:
            print(f"running for year {i}")
            export_import_url = wsda_urls['weekly_export_sales'].format(commodity, i,usda_api_key)
            data = download_api_data(export_import_url)
            data['market_year'] = i
            data.to_sql("usda_weekly_export_sales", engine, if_exists="append")
            print(f"downloaded data {data.shape}")


def download_onetime_data():
    commodities_url = wsda_urls['commodities']
    data = download_api_data(commodities_url)
    data.to_sql("commodities", engine, if_exists="replace")
    commodities_url = wsda_urls['countries']
    data = download_api_data(commodities_url)
    data.to_sql("countries", engine, if_exists="replace")
    return data


if __name__ == '__main__':
    main()
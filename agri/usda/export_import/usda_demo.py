import requests
import pandas as pd

if __name__ == '__main__':
    usda_api_key = r'6RjRbss6GkLCrlIJcufASzopCFx7Qo2ctLM0WcFO'
    url = f'https://api.fas.usda.gov/api/esr/commodities?api_key={usda_api_key}'
    resp = requests.get(url)
    commodities_esr_df = pd.DataFrame(resp.json())

    usda_api_key = r'6RjRbss6GkLCrlIJcufASzopCFx7Qo2ctLM0WcFO'
    url = f'https://api.fas.usda.gov/api/psd/commodities?api_key={usda_api_key}'
    resp = requests.get(url)
    commodities_psd_df = pd.DataFrame(resp.json())

    usda_api_key = r'6RjRbss6GkLCrlIJcufASzopCFx7Qo2ctLM0WcFO'
    url = f'https://api.fas.usda.gov/api/gats/commodities?api_key={usda_api_key}'
    resp = requests.get(url)
    commodities_gat_df = pd.DataFrame(resp.json())

    url = f'https://api.fas.usda.gov/api/psd/countries?api_key={usda_api_key}'
    resp = requests.get(url)
    countries_psd_df = pd.DataFrame(resp.json())

    marketYear=2024
    commodityCode=2631000
    countryCode= 'PK'

    url  = f'https://api.fas.usda.gov/api/psd/commodity/{commodityCode}/country/{countryCode}/year/{marketYear}/month/6?api_key={usda_api_key}'

    resp = requests.get(url)
    com_details_psd_df = pd.DataFrame(resp.json())
    print(com_details_psd_df)
    print(resp)
import numpy as np
import pandas as pd
from agri.database.dao.base_dao import fetch_df

# Replace these with real USDA ingestion (FAS API/CSV, NASS QuickStats, WASDE PDFs/CSV)

def load_weekly_exports_old(commodity: str = "Cotton", weeks: int = 52) -> pd.DataFrame:
    np.random.seed(0)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=weeks, freq="W-THU")
    countries = [
        "China","Vietnam","Pakistan","Bangladesh","Turkey",
        "Indonesia","Mexico","Thailand","India","Others"
    ]
    df = pd.DataFrame({
        "week": np.repeat(dates, len(countries)),
        "country": countries * len(dates),
        "net_sales": np.random.randint(0, 200, size=len(dates) * len(countries)) * 100,
        "shipments": np.random.randint(0, 250, size=len(dates) * len(countries)) * 100,
        "commodity": commodity,
        "my": "2024/25",
    })
    return df

def get_marketing_years(commodity_name: str):
    sql = """
    SELECT DISTINCT market_year
    FROM public.usda_weekly_export_sales wes
    JOIN public.commodities cm 
      ON wes."commodityCode" = cm."commodityCode"
    WHERE cm."commodityName" = %(commodity)s
    ORDER BY market_year DESC
    """
    return fetch_df(sql, {"commodity": commodity_name})["market_year"].tolist()

def load_weekly_exports(commodity_name: str):
    """
    Returns a DataFrame with columns:
    week, country, net_sales, shipments, commodity, my
    """
    sql = """
    SELECT 
        to_date(wes."weekEndingDate", 'YYYY-MM-DD') AS week,
        c."countryName" AS country,
        wes."currentMYNetSales" AS net_sales,
        wes."weeklyExports" AS shipments,
        cm."commodityName" AS commodity,
        wes.market_year AS my
    FROM public.usda_weekly_export_sales wes
    JOIN public.countries c ON wes."countryCode" = c."countryCode"
    JOIN public.commodities cm ON wes."commodityCode" = cm."commodityCode"
    WHERE cm."commodityName" = %(commodity)s
    ORDER BY week
    """
    data = fetch_df(sql, {"commodity": commodity_name})
    return data



def load_wasde_balance(commodity: str = "Cotton") -> pd.DataFrame:
    comps = ["Beginning Stocks", "Production", "Imports", "Total Supply", "Domestic Use", "Exports", "Ending Stocks"]
    vals = [4.3, 15.0, 0.5, 19.8, 2.5, 12.8, 4.5]
    prior = [4.2, 14.8, 0.5, 19.5, 2.6, 12.6, 4.3]
    last_year = [3.8, 14.2, 0.6, 18.6, 2.4, 12.2, 4.0]
    return pd.DataFrame({
        "component": comps,
        "current": vals,
        "prior": prior,
        "last_year": last_year,
        "commodity": commodity,
    })


def load_crop_progress(commodity: str = "Cotton") -> pd.DataFrame:
    states = ["TX", "GA", "MS", "AR", "NC", "AZ", "CA", "LA", "MO", "OK"]
    weeks = pd.date_range("2025-04-01", periods=20, freq="W-MON")
    df = []
    rng = np.random.default_rng(123)
    for st in states:
        for w in weeks:
            df.append({
                "state": st,
                "week": w,
                "planted": np.clip(rng.normal(80, 15), 0, 100),
                "squaring": np.clip(rng.normal(50, 20), 0, 100),
                "setting_bolls": np.clip(rng.normal(30, 20), 0, 100),
                "condition_good_excellent": np.clip(rng.normal(55, 10), 0, 100),
            })
    return pd.DataFrame(df)
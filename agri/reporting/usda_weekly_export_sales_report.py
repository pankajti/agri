import pandas as pd
import numpy as np


key_columns = {'market_year', 'countryCode', 'commodityCode', 'weekEndingDate'}

report_table_index = ['table', 'section' , 'unit', 'crop_year', 'total', 'top11', 'top5', 'vietnam',
                      'china', 'turkey', 'indonasia','turkey','indonasia' ,'mexico', 'india','paksitan','korea', 'bangladesh', 'thailand','taiwan']

def get_data(table_name='Upland NMY Commitment and Weekly Sales'):
       data = {'table': [table_name] * 6,
               'section': ['Total Commitment', 'Total Commitment', 'Commitment Untill Week 49',
                           'Commitment Untill Week 49', 'Commitment Untill Week 49', 'Net Sales'],
               'unit': ['Million 480 Bales', 'Million 480 Bales', 'Million 480 Bales', 'Million 480 Bales',
                        'Million 480 Bales', '480 Bales'],
               'crop_year': ['2022', '2023', '2022', '2023', '2024', 'in Wk 49'],
               'total': None,
               'top11': None,
               'top5': None,
               'vietnam': None,
               'china': None,
               'turkey': None,
               'indonasia': None,
               'mexico': None,
               'india': None,
               'pakistan': None,
               }

       report_template = pd.DataFrame(columns=report_table_index)
       report_template['table'] = table_name
       data = pd.DataFrame(data).T

       data.iloc[4:, :] = np.round(np.random.random((10, 6)), 2)
       return data.T


if __name__ == '__main__':
       data = get_data('Upland NMY Commitment and Weekly Sales')
       print(data)

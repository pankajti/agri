
import os

#text_file_path = r'/Users/pankajti/dev/git/agri/data/downloaded_reports/2025/wasde0225_TXT.txt'

import pandas as pd

root_dir = r'/Users/pankajti/dev/git/agri/data/downloaded_reports'

def get_file_paths():
    years = range(2014, 2026)
    all_text_files =[]
    all_excel_files =[]

    for year in years:
        file_path = os.path.join(root_dir,str(year))
        excel_files =sorted( [os.path.join(file_path, f) for f in os.listdir(file_path) if f.endswith('xls')])
        for  excel_file in  excel_files:
            print(excel_file, os.path.exists(excel_file))
            all_text_files.append(excel_file)

    return all_text_files

from xlrd import open_workbook

def read_excel_file(exel_file ):
    wb = open_workbook(exel_file)
    sheets = wb.sheets()
    sheet = sheets[0]
    number_of_rows = sheet.nrows
    sheet1= sheets[1]
    # for row in range(0,10):
    #     for col in range(0,10):
    #         print(sheet1.cell(row,col),row,col)

    date = sheet1.cell(0,0).value


    for row in range(0,number_of_rows) :
        val = sheet.cell(row, 0).value
        if val.lower().startswith('wheat'):
            ret_val = val + sheet.cell(row+1, 0).value
            return val ,date


import datetime as dt

def main():
    files = get_file_paths()
    all_recs = []
    for excelf in files:
        date = excelf.split("/")[-1][6:-8]
        dfe , date = read_excel_file(excelf)

        rec= {'date':date, 'text':dfe}
        all_recs.append(rec)

    text_df = pd.DataFrame(all_recs)
    text_df.to_csv("wheat_text.csv")
    print(text_df)


if __name__ == '__main__':
    main()


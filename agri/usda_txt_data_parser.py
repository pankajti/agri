
import os

#text_file_path = r'/Users/pankajti/dev/git/agri/data/downloaded_reports/2025/wasde0225_TXT.txt'

import pandas as pd

root_dir = r'/Users/pankajti/dev/git/agri/data/downloaded_reports'

def get_file_paths():
    years = range(2017, 2026)
    all_text_files =[]
    all_excel_files =[]

    for year in years:
        file_path = os.path.join(root_dir,str(year))
        files = sorted([os.path.join(file_path, f) for f in os.listdir(file_path) if f.endswith('txt')])
        excel_files =sorted( [os.path.join(file_path, f) for f in os.listdir(file_path) if f.endswith('xls')])
        for text_file,excel_file in zip(files,excel_files):
            print(text_file, os.path.exists(text_file))
            print(excel_file, os.path.exists(excel_file))
            all_text_files.append((text_file,excel_file))

    return all_text_files

from xlrd import open_workbook

def read_excel_file(exel_file ):
    wb = open_workbook(exel_file)
    sheets = wb.sheets()
    sheet = sheets[0]
    number_of_rows = sheet.nrows

    for row in range(0,number_of_rows) :
        val = sheet.cell(row, 0).value
        if val.lower().startswith('wheat'):
            return val



def read_text_file(text_file_path):
    start = False
    end = False
    snd = []

    counter = 0
    with open(text_file_path) as f:
        print(f"start for {text_file_path}")

        lines = f.readlines()
        for l in lines:
            if start:
                if not l.startswith(" "):
                    end = True
                if not end:
                    components = l.split()

                    if counter == 0:
                        components.insert(1, '')
                        components.insert(len(components),'data')
                    elif counter == 2:
                        year = components[0]
                        counter = counter + 1
                        continue

                    elif counter == 3 or counter == 4:
                        components.insert(0, year)
                        components.insert(len(components),'projected')

                    else:
                        components.insert(len(components),'estimate')
                    snd.append(components)
                    counter = counter + 1
                    print(components, len(components))

            if l.startswith('Wheat'):
                start = True


    df = pd.DataFrame(snd, columns=['year', 'month', 'Output', 'Supply', 'Trade 2/', 'Use 3/', 'Stocks','type'])

    return df

def main():
    files = get_file_paths()
    dfs = []
    for f, excelf in files:
        df = read_text_file(f)
        dfs.append(df)
        dfe = read_excel_file(excelf)
        print(dfe)
    all_dfs = pd.concat(dfs)
    all_dfs.to_csv("wheat_all_data.csv")

    print(all_dfs)


if __name__ == '__main__':
    main()


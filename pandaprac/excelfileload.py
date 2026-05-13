#pip install pandas sqlalchemy pyodbc openpyxl
#for  multiple sheet in file https://github.com/data-geek-lab/insert-excel-sheets-into-sql
# for dba https://github.com/lorenzouriel/data-eyes
import pandas as pd
from sqlalchemy import create_engine
import urllib

excel_file = 'G:\insert-excel-sheets-into-sql-main\sample_sales_data.xlsx' 

# 1. Load the Excel file
df = pd.read_excel(excel_file, sheet_name='Employees', engine='openpyxl')

# 2. Define connection parameters
server = 'NilMSI'
database = 'TestDb'
driver = '{ODBC Driver 17 for SQL Server}' # Ensure this driver is installed

# 3. Create the SQLAlchemy engine
connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
params = urllib.parse.quote_plus(connection_string)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

# 4. Load data into SQL Server
# if_exists options: 'fail', 'replace', or 'append'
df.to_sql('target_table_name', con=engine, if_exists='replace', index=False)
print("Data has been loaded into SQL Server successfully.")
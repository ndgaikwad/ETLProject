import pandas as pd
import sqlalchemy
import pyodbc
import os
#os.chdir(r'D:\testdata')
#print(os.getcwd())  # Verify the current working directory
#print(os.listdir())  # List files in the current directory to confirm the CSV file is present

#print (pyodbc.drivers())  # Print available ODBC drivers to verify the correct one is installed

# Example usage
csv_file_path = 'D:\\testdata\\advertising_test.csv'  # Replace with your actual CSV file name
table_name = 'advertising_data'  # Replace with your actual table name
connection_string = f'mssql+pyodbc://testdbserver/TestDBname?trusted_connection=yes&driver=ODBC Driver 17 for SQL Server'
print (connection_string)  # Print the connection string to verify it's correct
print (os.path.exists(csv_file_path))  # Check if the CSV file exists at the specified path
# Create a SQLAlchemy engine
engine = sqlalchemy.create_engine(connection_string)
print
# Read the CSV file into a DataFrame
df = pd.read_csv(csv_file_path)
print(df.head())  # Display the first few rows of the DataFrame to verify it was loaded correctly
# Load the DataFrame into the SQL Server table
df.to_sql(table_name, con=engine, if_exists='append', index=False)

print(f"Data from {csv_file_path} has been loaded into the {table_name} table in SQL Server.")

df = pd.read_sql(f"SELECT * FROM {table_name}", con=engine)
print(df.head())  # Display the first few rows of the DataFrame to verify it was loaded correctly

'''
Author : Andreas Makrides 
'''

import os
import pandas as pd
#remove warnings
import warnings
warnings.filterwarnings("ignore")

def create_dataframes_from_csv(folder_path):
    # Get a list of all subfolders in the given folder path
    subfolders = [f.path for f in os.scandir(folder_path) if f.is_dir()]

    # Iterate over the subfolders
    for subfolder in subfolders:
        subfolder_name = os.path.basename(subfolder)
        dfs = []

        # Get a list of CSV files in the current subfolder
        csv_files = [f for f in os.listdir(subfolder) if f.endswith('.csv')]

        # Iterate over the CSV files in the subfolder
        for csv_file in csv_files:
            file_path = os.path.join(subfolder, csv_file)

            # Read the CSV file and create a DataFrame
            df = pd.read_csv(file_path)

            # Append the DataFrame to the list
            dfs.append(df)

        # Create a DataFrame with the subfolder name
        merged_df = pd.concat(dfs, axis=0)
        merged_df.drop(['RepeatedHourFlag'], axis=1, inplace=True)
        merged_df.set_index('SettlementPoint', inplace=True)
        
        # Use the subfolder name as the DataFrame name
        globals()[subfolder_name] = merged_df
        

# Provide the folder path containing the subfolders and CSV files
folder_path = r"C:\Users\user\OneDrive - University of Cyprus\Texas Exchange Program\Conference Paris\scrappy_data\raw data"

# Call the function to create the DataFrames
create_dataframes_from_csv(folder_path)
    
# Get a list of CSV files in the folder
file_list = sorted(os.listdir(folder_path), reverse=True)

# Create an empty list to store the dataframes
new_df = []
final = pd.DataFrame()
# Iterate through the CSV files in reverse order
for file_name in file_list:
    if file_name.endswith('.csv'):
        # Construct the full file path
        file_path = os.path.join(folder_path, file_name)
        
        # Read the CSV file into a dataframe
        df = pd.read_csv(file_path)
        
        df.drop(['RepeatedHourFlag'], axis=1, inplace=True)
        df.set_index('SettlementPoint', inplace=True)
        
        # # Perform the desired operation on the dataframe
        final.insert(0, df["SCEDTimestamp"][0], df["LMP"])
        
        # Append the modified dataframe to the list
        new_df.append(df)
        
#take a part of the nodes that are on the load zone west  
LZ_WEST_nodes = ["LZ_WEST","AEEC","BCATWD_WD_1","BLSMT1_5_A_6","BOOTLEG_UN1","BRISCOE_WIND","CASL_GAP_UN1","CFLATS_UNIT","CN_BRKS_UNT1","COTPLNS_RN","ELECTRAW_1_2","FOARDCTY_ALL","GPASTURE_ALL","GRANDVW1_A_B","HICK_G1_G2","HORSECRK_RN","HOVEY_GEN","HRFDWIND_ALL","HWF_HWFG1","INDN_INDNNWP","KEO_KEO_SM1","LAMESASLR_G","LASSO_GEN","LGD_LANGFORD","LHORN_N_U1_2","LNCRK_ALL","MARIAH_ALL","MESQCRK_ALL","MIAM1_G1_G2","MISAE_GEN_RN","MOZART_WIND1","NBOHR_RN","NWF_NWF1","OECCS_1","PB2SES_CT1","PH1_UNIT1_2","PHOEBE_ALL","RANCHERO_ALL","REROCK_ALL","RIGGIN_UNIT1","RN_ECEC_HOLT","ROUTE66_RN","RSK_RN","SALVTION_GEN","SLTFRK_UN1_2","SOLARA_UNIT1","SPLAIN1_RN","SPLAIN2_RN","SRWE1_UNIT1","SSPURT_WIND1","SWEC_G1","S_HILLS_RN","TAHOKA_ALL","TRINITY_ALL","WAKEWE_ALL","WAYMARK_RN","WEC_WECG1","WFCOGEN_CC1","WL_RANCH_RN","W_PECO_UNIT1"]
df_filtered = final[final.index.isin(LZ_WEST_nodes)]

#reorder the columns of dataframes
columns = df_filtered.columns[::-1]
df_filtered = df_filtered[columns]

#format data
row_index = df_filtered.index.get_loc('LZ_WEST')
first_row = df_filtered.iloc[row_index]
df_filtered = pd.concat([first_row.to_frame().T, df_filtered.drop('LZ_WEST')])

#Profit = Price_Difference*Quantity_of_Electricity

#Price Difference Calculation
Price_Diff = df_filtered.copy()
for column in Price_Diff.columns:
    first_value = Price_Diff[column].iloc[0]  # Get the first value of the column
    Price_Diff[column][1:] = Price_Diff[column][1:] - first_value
 
#Define the Quantity of Electricity
Quantity_of_Electricity = 0.25

#Profit Calculation
Profit = df_filtered.copy()
for column in Profit.columns:
    Profit[column][1:] = Price_Diff[column][1:] * Quantity_of_Electricity



#export the 3 dataframes
dataframes = [Profit, Price_Diff, df_filtered]

# Specify the base file path for the Excel files
base_file_path = r'C:\Users\user\OneDrive - University of Cyprus\Texas Exchange Program\Conference Paris\scrappy_data\raw data'

# Iterate through the dataframes and save each one as an Excel file
for i, df in enumerate(dataframes):
    # Construct the file path for each Excel file
    file_path = f"{base_file_path}_{i+1}.xlsx"
    
    # Export the dataframe to Excel with the string index
    df.to_excel(file_path, index=True, index_label="Index")

# AND/OR 
#Export each dataframe, each excel sheet is a different date
df = Profit.copy()
# Convert column names to datetime objects
df.columns = pd.to_datetime(df.columns)
# Group columns by date
columns_by_date = df.columns.date
# Create separate dataframes for each date
date_dataframes = {}
for date in set(columns_by_date):
    date_columns = [col for col in df.columns if col.date() == date]
    date_df = df[date_columns]
    date_dataframes[date] = date_df

with pd.ExcelWriter('Profit.xlsx') as writer:
    for date, date_df in date_dataframes.items():
        columns = date_df.columns[::-1]
        date_df = date_df[columns]
        date_df.to_excel(writer, sheet_name=str(date), index=True)
        

#Export each dataframe, each excel sheet is a different date
df = Price_Diff.copy()
# Convert column names to datetime objects
df.columns = pd.to_datetime(df.columns)
# Group columns by date
columns_by_date = df.columns.date
# Create separate dataframes for each date
date_dataframes = {}
for date in set(columns_by_date):
    date_columns = [col for col in df.columns if col.date() == date]
    date_df = df[date_columns]
    date_dataframes[date] = date_df

with pd.ExcelWriter('Price_Diff.xlsx') as writer:
    for date, date_df in date_dataframes.items():
        columns = date_df.columns[::-1]
        date_df = date_df[columns]
        date_df.to_excel(writer, sheet_name=str(date), index=True)
        
        
#Export each dataframe, each excel sheet is a different date
df = df_filtered.copy()
# Convert column names to datetime objects
df.columns = pd.to_datetime(df.columns)
# Group columns by date
columns_by_date = df.columns.date
# Create separate dataframes for each date
date_dataframes = {}
for date in set(columns_by_date):
    date_columns = [col for col in df.columns if col.date() == date]
    date_df = df[date_columns]
    date_dataframes[date] = date_df

with pd.ExcelWriter('Nodal_Price.xlsx') as writer:
    for date, date_df in date_dataframes.items():
        columns = date_df.columns[::-1]
        date_df = date_df[columns]
        date_df.to_excel(writer, sheet_name=str(date), index=True)

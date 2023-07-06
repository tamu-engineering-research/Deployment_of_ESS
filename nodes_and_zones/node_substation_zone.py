# -*- coding: utf-8 -*-
"""
Created on Thu Jul  6 16:24:44 2023

@author: Andreas Makrides
"""
import pandas as pd

# Load the first Excel file with "RESOURCE_NODE" and "UNIT_SUBSTATION" columns
df1 = pd.read_csv(r"C:\Users\user\OneDrive - University of Cyprus\Texas Exchange Program\Conference Paris\nodes_and_zones\Resource_Node_to_Unit.csv")

# Load the second Excel file with "SUBSTATION" and "SETTLEMENT_LOAD_ZONE" columns
df2 = pd.read_csv(r"C:\Users\user\OneDrive - University of Cyprus\Texas Exchange Program\Conference Paris\nodes_and_zones\Settlement_Points.csv") 

# Merge the two DataFrames based on the common column "UNIT_SUBSTATION"
merged_df = pd.merge(df1, df2, left_on='UNIT_SUBSTATION', right_on='SUBSTATION', how='left')

# Extract the "RESOURCE_NODE", "UNIT_SUBSTATION", and "SETTLEMENT_LOAD_ZONE" columns
result_df = merged_df[['RESOURCE_NODE', 'UNIT_SUBSTATION', 'SETTLEMENT_LOAD_ZONE']]

# Save the result to a new Excel file
result_df.to_excel('result.xlsx', index=False)  # Replace 'result.xlsx' with the desired output filename or path


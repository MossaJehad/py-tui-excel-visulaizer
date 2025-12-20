
import pandas as pd
import os
import numpy as np

file_path = "xlsx/HR.xlsx"
if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

try:
    df = pd.read_excel(file_path)
    print("Columns:", df.columns.tolist())
    print("Head:\n", df.head())

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    print("Numeric Cols:", numeric_cols)

    cat_cols = df.select_dtypes(include=['object']).columns.tolist()
    print("Cat Cols:", cat_cols)

except Exception as e:
    print("Error reading excel:", e)

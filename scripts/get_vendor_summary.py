import pandas as pd
import sqlite3
import logging
import time
from db_ingestion import ingest_db

logging.basicConfig(
    filename = "logs/get_vendor_summary.log",
    level = logging.DEBUG,
    format = "%(asctime)s - %(levelname)s - %(message)s",
    filemode = "a"
)

def create_vendor_summary(conn):
    # Merge different tables to get overall vendor summary
    vendor_sales_summary = pd.read_sql_query("""WITH FreightSummary AS(
    SELECT
        VendorNumber,
        SUM(Freight) AS FreightCost
    FROM vendor_invoice
    GROUP BY VendorNumber
    ),
    PurchaseSummary AS (
    SELECT
        p.VendorNumber,
        p.VendorName,
        p.Brand,
        p.Description,
        p.PurchasePrice,
        pp.Volume,          
        pp.Price as ActualPrice,          
        SUM(p.Quantity) as TotalPurchaseQuantity,
        SUM(p.Dollars) as TotalPurchaseDollars
    FROM purchases p
    JOIN purchase_prices pp
        ON p.brand = pp.brand
        WHERE p.PurchasePrice > 0
    GROUP BY p.VendorNumber, p.VendorName, p.Brand, p.Description, p.PurchasePrice, pp.Price, pp.Volume
    ),
    SalesSummary AS (
    SELECT
        VendorNo,
        Brand,
        SUM(SalesDollars) as TotalSalesDollars,
        SUM(SalesPrice) as TotalSalesPrice,
        SUM(SalesQuantity) as TotalSalesQuantity,
        SUM(ExciseTax) as TotalExciseTax
    FROM sales
    GROUP BY VendorNo, Brand
    )
    SELECT
        ps.VendorNumber,
        ps.VendorName,
        ps.Brand,
        ps.Description,
        ps.PurchasePrice,
        ps.ActualPrice,
        ps.Volume,
        ps.TotalPurchaseQuantity,
        ps.TotalPurchaseDollars,
        ss.TotalSalesQuantity,
        ss.TotalSalesDollars,
        ss.TotalSalesPrice,
        ss.TotalExciseTax,
        fs.FreightCost
    FROM PurchaseSummary ps
    LEFT JOIN SalesSummary ss
        ON ps.VendorNumber = ss.VendorNo
        AND ps.Brand = ss.Brand
    LEFT JOIN FreightSummary fs
        ON ps.VendorNumber = fs.VendorNumber
    ORDER BY ps.TotalPurchaseDollars DESC""", conn)

    return vendor_sales_summary

def clean_data(summary_df):
    # Changing volume datatype to float
    summary_df['Volume'] = summary_df['Volume'].astype('float64')     
    
    # Filling missing values with 0
    summary_df.fillna(0, inplace = True)
    
    # Removing spaces from categorical columns
    summary_df['VendorName'] = summary_df['VendorName'].str.strip()
    summary_df['Description'] = summary_df['Description'].str.strip()
    
    # Creating new columns for further analysis
    summary_df['GrossProfit'] = summary_df['TotalSalesDollars'] - summary_df['TotalPurchaseDollars']
    summary_df['ProfitMargin'] = (summary_df['GrossProfit'] / summary_df['TotalSalesDollars']) * 100
    summary_df['StockTurnover'] = summary_df['TotalSalesQuantity'] / summary_df['TotalPurchaseQuantity']
    summary_df['SalesToPurchaseRatio'] = summary_df['TotalSalesDollars'] / summary_df['TotalPurchaseDollars']    

    return summary_df

if __name__ == '__main__':
    conn = sqlite3.connect('inventory.db')
    logging.info('Creating Vendor Summary Table')
    summary_df = create_vendor_summary(conn)
    logging.info(summary_df.head())

    logging.info('Cleaning Data')
    clean_df = clean_data(summary_df)
    logging.info(clean_df.head())

    logging.info('Ingesting Data') # Corrected from logging_info
    # Make sure 'db_ingestion' module and 'ingest_db' function are correctly implemented and accessible
    ingest_db(clean_df,'vendor_sales_summary', conn) 
    logging.info('Ingestion Completed')

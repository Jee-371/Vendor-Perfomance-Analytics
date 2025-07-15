import pandas as pd
import os
from sqlalchemy import create_engine
import logging
import time

logging.basicConfig(
    filename = "logs/.log",
    level = logging.DEBUG,
    format = "%(asctime)s - %(levelname)s - %(message)s",
    filemode = "a"
)

engine = create_engine('sqlite:///inventory.db')

def ingest_db(df, table_name, engine):
    df.to_sql(table_name, con = engine, if_exists = 'replace', index = False)

def load_raw_data():
    startt = time.time()
    for file in os.listdir('data'):
        if '.csv' in file:
            df = pd.read_csv('data/'+file)
            logging.info(f'Ingesting {file} in db')
            ingest_db(df, file[:-4], engine)
    endt = time.time()
    totalt = (endt-startt)/60
    logging.info('-------------Ingestion Complete-------------')
    logging.info(f'Time taken: {totalt} minutes')

if __name__ == '__main__':
    load_raw_data()

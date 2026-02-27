#!/usr/bin/env python
# coding: utf-8


import click
import pandas as pd
import psycopg
from sqlalchemy import create_engine
from tqdm.auto import tqdm

# Define dtype for the yellow taxi data
dtype = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

# Define dtype for the taxi zone lookup data
taxi_zone_lookup_dtype = {
    "LocationID": "Int64",
    "Borough": "string",
    "Zone": "string",
    "service_zone": "string"
}

parse_dates = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime"
]




@click.command()
@click.option('--pg-user', default='root', help='PostgreSQL user')
@click.option('--pg-pass', default='root', help='PostgreSQL password')
@click.option('--pg-host', default='localhost', help='PostgreSQL host')
@click.option('--pg-port', default=5432, type=int, help='PostgreSQL port')
@click.option('--pg-db', default='ny_taxi', help='PostgreSQL database name')
@click.option('--year', default=2021, type=int, help='Year of the data')
@click.option('--month', default=1, type=int, help='Month of the data')
@click.option('--chunksize', default=100000, type=int, help='Chunk size for reading CSV')
@click.option('--target-table', default='yellow_taxi_data', help='Target table name')
def run(pg_user, pg_pass, pg_host, pg_port, pg_db, year, month, chunksize, target_table):

    prefix_trips = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/'
    prefix_zones = 'https://d37ci6vzurychx.cloudfront.net/misc/'
    taxi_data_url = f'{prefix_trips}yellow_tripdata_{year}-{month:02d}.csv.gz'
    taxi_zone_lookup_url = f'{prefix_zones}taxi+_zone_lookup.csv'
    #url = f'{prefix}/yellow_tripdata_{year}-{month:02d}.csv.gz'

    engine = create_engine(
        f'postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}')


    #Ingest taxi zone lookup data in chunks
    taxi_zone_df_iter = pd.read_csv(
        taxi_zone_lookup_url, 
        dtype=taxi_zone_lookup_dtype, 
        iterator=True, 
        chunksize=chunksize)

    first=True
    for df_zone_chunk in tqdm(taxi_zone_df_iter):
        if first:
            df_zone_chunk.head(0).to_sql(
                name='taxi_zone_lookup', 
                con=engine, 
                if_exists='replace'
            )
            first = False

        df_zone_chunk.to_sql(
            name='taxi_zone_lookup', 
            con=engine, 
            if_exists='append')


    #Ingest yellow taxi trip data
    df_iter = pd.read_csv(
        taxi_data_url,
        dtype=dtype,
        parse_dates=parse_dates,
        iterator=True,
        chunksize=chunksize )



    first=True
    for df_chunk in tqdm(df_iter):
        if first:
            df_chunk.head(0).to_sql(
                name=target_table, 
                con=engine, 
                if_exists='replace'
            )
            first = False

        df_chunk.to_sql(
            name=target_table, 
            con=engine, 
            if_exists='append')

if __name__ == '__main__':
    run()






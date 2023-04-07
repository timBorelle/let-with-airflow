from __future__ import annotations

import airflow
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.decorators import dag, task
from datetime import timedelta

import pandas as pd
import numpy as np
import psycopg2
from sqlalchemy import create_engine
#from sqlalchemy.engine import Engine, Connection
from sqlalchemy.engine.base import Engine

import xgboost as xgb
import logging
import json
import pendulum

#from sklearn import preprocessing

logging.basicConfig()
logger = logging.getLogger("logs")
logger.setLevel(logging.INFO)

default_args = {
    'start_date': airflow.utils.dates.days_ago(0),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

@dag(
    'let_data',    
    default_args=default_args,
    #schedule=None,
    schedule_interval='1 * * * 1',
    start_date=pendulum.datetime(2023, 3, 6, tz="UTC"),
    catchup=False,
    tags=["load","extract","transform","train"],
)
def let_data():
    columns = [
        "age", "class_of_worker", "education", "wage_per_hour", "enrolled_in_edu_inst_last_wk", 
        "marital_status", "major_industry_code", "major_occupation_code", "race", "hispanic_origin", "sex", "member_of_a_labor_union", 
        "reason_for_unemployment", "full_or_part_time_employment", "capital_gains", "capital_losses", "divdends_from_stocks", 
        "tax_filer_status", "region_of_previous_residence", "state_of_previous_residence", "detailed_household_and_family", 
        "detailed_household_summary_in_household", 
        "instance_weight",                  # metadata : ignore.
        "migration_code_change_in_msa",     # ?
        "migration_code_change_in_reg",     # ?
        "migration_code_move_within_reg",   # ?
        "live_in_this_house_1_year_ago", "migration_prev_res_in_sunbelt", "num_persons_worked_for_employer", "family_members_under_18", 
        "country_of_birth_father", "country_of_birth_mother", "country_of_birth_self", "citizenship", "own_biz_or_self_employed", 
        "fill_inc_questionnaire_for_veteran", "veterans_benefits", "weeks_worked_in_year", "year", "total_person_income"
    ]

    def read_data(data_file_path: str, columns_name: list) -> pd.DataFrame:
        try:
            if columns_name != None:
                logger.info("read_data : .csv file doesn't contains header !")
                df = pd.read_csv(
                    data_file_path,
                    names=columns_name
                )
            else:
                df = pd.read_csv(
                    data_file_path
                )
            return df.dropna()
        except ValueError as ve:
            logger.error("Incorrect data format. " + str(ve))
            exit(1)
        except TypeError as te:
            logger.error("Incorrect data type. " + str(te))
            exit(1)

    def get_connection():
        return create_engine(
            url="postgresql://postgres:postgres@pg_container:5432/census"
        )

    @task()
    def loadDataToDB() -> bool:
        conn = psycopg2.connect(database="census",
            user='postgres', password='postgres', 
            host='pg_container', port='5432'
        )
        print(conn)
        conn.autocommit = True
        cursor = conn.cursor()
        sql = '''CREATE TABLE IF NOT EXISTS CENSUS_INCOME_TEST(age smallint NOT NULL, class_of_worker varchar(50), industry_recode smallint,\
            occupation_recode smallint, education varchar(50), wage_per_hour smallint, enrolled_in_edu_inst_last_wk varchar(50),\
            marital_status varchar(50), major_industry_code varchar(50), major_occupation_code varchar(50), race varchar(50),\
            hispanic_origin varchar(50), sex varchar(50), member_of_a_labor_union varchar(50), reason_for_unemployment varchar(50),\
            full_or_part_time_employment varchar(50), capital_gains int, capital_losses int, divdends_from_stocks int,\
            tax_filer_status varchar(50), region_of_previous_residence varchar(50), state_of_previous_residence varchar(50),\
            detailed_household_and_family varchar(50), detailed_household_summary_in_household varchar(50), instance_weight decimal,\
            migration_code_change_in_msa varchar(50), migration_code_change_in_reg varchar(50), migration_code_move_within_reg varchar(50),\
            live_in_this_house_1_year_ago varchar(50), migration_prev_res_in_sunbelt varchar(50), num_persons_worked_for_employer varchar(50),\
            family_members_under_18 varchar(50), country_of_birth_father varchar(50), country_of_birth_mother varchar(50),\
            country_of_birth_self varchar(50), citizenship varchar(50), own_biz_or_self_employed smallint,\
            fill_inc_questionnaire_for_veteran varchar(50), veterans_benefits smallint, weeks_worked_in_year smallint, year smallint,\
            total_person_income varchar(10));'''
        cursor.execute(sql)
        df = read_data("/app/data/us_census_full/census_income_test.csv", columns)
        engine = get_connection()
        # Save the data from dataframe to postgres table "census_income_test"
        df.to_sql(
            'census_income_test', 
            engine,
            index=False, # Not copying over the index
            if_exists='replace'
        )
        print("Loading finished.")
        conn.commit()
        conn.close()
        return True

    @task()
    def extractData(b: bool, file_path: str, columns: list):
        engine = get_connection()
        df = read_data(file_path, columns)
        df.to_sql(
            'census_income_train', 
            engine,
            index=False,
            if_exists='replace'
        )
        return True

    @task()
    def transformData(b: bool):
        df_list = ["train", "test"]
        engine = get_connection()
        for i in df_list:
            df = pd.read_sql_table('census_income_'+i, engine)  
            df["total_person_income"] = df["total_person_income"].replace(' - 50000.', -50000)
            df["total_person_income"] = df["total_person_income"].replace(' + 50000.', +50000)
            df["total_person_income"] = df["total_person_income"].replace(' 50000+.', +50000)
            df["total_person_income"] = pd.to_numeric(df["total_person_income"])
            df['total_person_income'] = df['total_person_income'].astype('int')
            list_new_name_features = {}
            list_new_name_features["sex"] = ["sex_ Female","sex_ Male"]
            list_new_name_features["marital_status"] = ["marital_stat_ Divorced","marital_stat_ Married-A F spouse present",
                                    "marital_stat_ Married-civilian spouse present","marital_stat_ Married-spouse absent",
                                    "marital_stat_ Never married","marital_stat_ Separated","marital_stat_ Widowed"]
            list_new_name_features["education"] = ["education_ 10th grade","education_ 11th grade","education_ 12th grade no diploma",
                                    "education_ 1st 2nd 3rd or 4th grade","education_ 5th or 6th grade","education_ 7th and 8th grade",
                                    "education_ 9th grade","education_ Associates degree-academic program",
                                    "education_ Associates degree-occup /vocational","education_ Bachelors degree(BA AB BS)",
                                    "education_ Children","education_ Doctorate degree(PhD EdD)","education_ High school graduate",
                                    "education_ Less than 1st grade","education_ Masters degree(MA MS MEng MEd MSW MBA)",
                                    "education_ Prof school degree (MD DDS DVM LLB JD)","education_ Some college but no degree"]
            list_new_name_features["tax_filer_status"] = ["tax_filer_stat_ Head of household","tax_filer_stat_ Joint both 65+",
                                    "tax_filer_stat_ Joint both under 65","tax_filer_stat_ Joint one under 65 & one 65+",
                                    "tax_filer_stat_ Nonfiler","tax_filer_stat_ Single"]
            feature_names_list_to_keep = ["age", "sex", "marital_status", "education", "tax_filer_status"]
            for c in columns:
                if c not in feature_names_list_to_keep:
                    df.drop(c, inplace=True, axis=1)
                elif c != "age" and c == "marital_status" or c == "sex" or c == "tax_filer_status" or c == "education":
                    for f in list_new_name_features[c]:
                        df[f] = df[c]
                        df[f] = df.apply(lambda r: 1 if r[c] in f else 0, axis=1)
                    df.drop(c, inplace=True, axis=1)   # uncomment in future
            df.to_sql(
                'census_income_d'+i, 
                engine,
                index=False,
                if_exists='replace'
            )
        return True

    @task()
    def trainModel(b: bool):
        df_list = ["train", "test"]
        engine = get_connection()
        df = {}
        for i in df_list:
            df[i] = pd.read_sql_table('census_income_d'+i, engine)
        # load model and data in
        bst = xgb.Booster(model_file="/app/data/xgbc.json")
        f_names = bst.feature_names
        dtrain = xgb.DMatrix(df["train"], feature_names=f_names)
        dtest = xgb.DMatrix(df["test"], feature_names=f_names)
        try:
            # Prediction
            ypred = pd.DataFrame(bst.predict(dtest), columns=["predictions"])
            print(f"ypred type : {type(ypred)}")
            ypred.to_sql(
                'census_income_predictions', 
                engine,
                index=False,
                if_exists='replace'
            )
            return True
        except ValueError as ve:
            print(ve)
            return False

    @task()
    def getStatisticalAnalysis(b: bool):
        engine = get_connection()
        df_predictions = pd.read_sql_table('census_income_predictions', engine)
        print(df_predictions[["predictions"]].describe())

    b1 = loadDataToDB()
    train_file_path = "/app/data/us_census_full/census_income_learn.csv"
    #test_file_path = "/app/data/us_census_full/census_income_test.csv"
    b2 = extractData(b1, train_file_path, columns)
    b3 = transformData(b2)
    b4 = trainModel(b3)
    getStatisticalAnalysis(b4)

let_data()

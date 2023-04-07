# Data engineer interview

Hello!

If you're here, you're probably applying to work with us at Chronotruck. At the time, we're looking for a data engineer role and this test is to ensure that we could work together.

## The test

The goal of this test is to evalute a dataset, store it in a RDMS, use and apply a machine learning model to it and track its performance.
The US Census dataset contains detailed but anonymized information for approximately 300,000 people.
The archive contains 3 files: a large learning .csv file, a test.csv file and a metadata file describing the columns of the two above mentioned files (identical for both)

We expect to be able to run all the stack localy using containers.

At Chronotruck we use [Airflow](https://airflow.apache.org/), and so, we would like you to use it to transform and analyse the data.

### ML pipeline

The first task is to load the provided dataset (test), which can be found under the `data directory`, in an RDMS table so that it can be queried with ease.
Let's say we receive a dataset with this schema from operations on a daily basis.

After the data has been loaded, you must apply the provided machine learning model, which has been trained on the training set, to a dataset containing the 'age', 'sex', 'marital staus', 'education', and 'tax_filer_status' columns and store the results in a dedicated RDBMS table. This table must contain the model's features along with the predicted variable.

Finaly we need to track the model's performance over time.

### Business inteligence

Our sales team needs to have some insights for our clients and so please provide a basic statistical analysis of this test set on a wekly basis.

## Summary

1.  Store the data in a RDMS System.
2.  Use Airflow to load, transform, analyze the data and apply the machine learning model.
3.  Store the results of the model in the RDMS system.
4.  Provide a basic statistical analysis of the data.


## Load, extract and transform (LET) census data, then train a model with Airflow

### Build project
```bash
make install
```

### Launch (build and start all containers)
```bash
./start.sh
```

### Restart all containers
```bash
./restart.sh
```

### Stop all containers
```bash
./stop.sh
```
### Trigger Airflow dag let_data with CLI 
docker exec -d $(docker ps | grep airflow | head -c 12) airflow dags trigger let_data

### Containers access 
#### Airflow dags access
http://localhost:8080/dags

Username / password: airflow / airflow 

#### Pgadmin4 access (Postgres database)
http://localhost:5050/

Username / password: admin@admin.com / root

##### Find SQL tables
Browser > Chronotruck > password: postgres > My Server > Databases > census > Schemas > public > Tables




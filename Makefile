.ONESHELL:

SHELL := /bin/bash

extract:
	cd data
	test -d us_census_full/census_income_learn.csv || unzip us_census_full.zip
	cd ..

install: extract
	chmod u+x *.sh docker/airflow/*.sh
	docker build -t airflow-base docker/airflow

clean:
	cd data
	rm -Rf __MACOSX us_census_full
	cd ..

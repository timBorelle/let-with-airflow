# Base Image
FROM apache/airflow:slim-latest-python3.8

ARG AIRFLOW_HOME=/opt/airflow

# Export the environment variable AIRFLOW_HOME where airflow will be installed
ENV AIRFLOW_HOME=${AIRFLOW_HOME}

# Copy files from host to container
COPY ./start-airflow.sh ./start-airflow.sh
COPY ./requirements.txt /app/requirements.txt

USER root
# Set the owner of the files in AIRFLOW_HOME to the user airflow
RUN chown -R airflow: ${AIRFLOW_HOME} /app && \
    chmod +x ./start-airflow.sh

# Set the username to use
USER airflow

# Install required Python packages
RUN pip install -r /app/requirements.txt

# Create the folder dags inside $AIRFLOW_HOME
RUN mkdir -p ${AIRFLOW_HOME}/dags /app/data

# Expose ports (just to indicate that this container needs to map port)
EXPOSE 8080

ENTRYPOINT [""]
# Execute start-airflow.sh
CMD [ "./start-airflow.sh" ]

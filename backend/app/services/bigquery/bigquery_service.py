"""Service to interact with the BigQuery API"""

import os
from typing import Optional
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError


class BigQueryService(object):
    """Service to interact with the BigQuery API"""

    def __init__(self, gcp_project_id):
        self.project_id = gcp_project_id

    def query(self, query, job_config: Optional[bigquery.QueryJobConfig] = None):
        """Executes a query"""
        try:
            bq_client = bigquery.Client(project=self.project_id)
            dataframe = bq_client.query(query, job_config=job_config).to_dataframe()
            print("Data loaded successfully into DataFrame.")
            print(dataframe.head())
            return dataframe
        except GoogleCloudError as e:
            print(f"An error occurred during BigQuery operation: {e}")
        except Exception as e:
            print(f"A general error occurred: {e}")


bigquery_service = BigQueryService(os.getenv("PROJECT_ID"))

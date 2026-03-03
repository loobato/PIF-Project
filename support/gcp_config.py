from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional

import pandas as pd
import streamlit as st
from google.cloud import bigquery, firestore
from google.oauth2 import service_account


ClientName = Literal["firebase", "bq"]


@dataclass
class Database:
    """
    Single entrypoint to GCP persistence.

    - client="firebase": Firestore (used for active games + players info)
    - client="bq": BigQuery (used to record finished games)

    Usage (recommended in app startup):
        db = Database(default_client="firebase")
        st.session_state["db"] = db

    Then anywhere:
        db = st.session_state["db"].use("bq")
        db.create("dw-fin.pif_project.game_table", df_game)
    """

    project_id: str = "dw-fin"
    default_client: ClientName = "firebase"
    credentials_secret_key: str = "gcp_service_account"

    _active: ClientName = "firebase"
    _credentials: Any = None
    _firestore: Optional[firestore.Client] = None
    _bigquery: Optional[bigquery.Client] = None

    def __post_init__(self) -> None:
        self._active = self.default_client
        self._credentials = self._load_credentials()

    def use(self, client: ClientName) -> "Database":
        self._active = client
        return self

    # ---------- credentials / clients ----------
    def _load_credentials(self) -> Any:
        try:
            info = st.secrets[self.credentials_secret_key]
            return service_account.Credentials.from_service_account_info(info)
        except Exception:
            return None

    @property
    def firestore(self) -> firestore.Client:
        if self._firestore is None:
            if self._credentials is None:
                raise RuntimeError("Firestore credentials not configured in Streamlit secrets.")
            self._firestore = firestore.Client(project=self.project_id, credentials=self._credentials)
        return self._firestore

    @property
    def bq(self) -> bigquery.Client:
        if self._bigquery is None:
            if self._credentials is None:
                raise RuntimeError("BigQuery credentials not configured in Streamlit secrets.")
            self._bigquery = bigquery.Client(project=self.project_id, credentials=self._credentials)
        return self._bigquery

    # ---------- unified CRUD API ----------
    def create(self, resource: str, data: Any, *, doc_id: Optional[str] = None) -> Any:
        """
        Create/insert.

        - firebase: resource=collection name, data=dict-like, doc_id optional (auto-id if omitted)
        - bq: resource=table_id, data=DataFrame or list[dict] (append)
        """
        if self._active == "firebase":
            if doc_id is None:
                return self.firestore.collection(resource).add(self._firestore_prepare(data))
            self.firestore.collection(resource).document(str(doc_id)).set(self._firestore_prepare(data))
            return str(doc_id)

        if isinstance(data, pd.DataFrame):
            # Convert DataFrame rows to JSON records to avoid pyarrow dtype issues
            records = data.to_dict(orient="records")
            errors = self.bq.insert_rows_json(resource, records)
            if errors:
                raise RuntimeError(f"BigQuery insert errors: {errors}")
            return True

        if isinstance(data, dict):
            data = [data]
        if isinstance(data, list):
            errors = self.bq.insert_rows_json(resource, data)
            if errors:
                raise RuntimeError(f"BigQuery insert errors: {errors}")
            return True

        raise TypeError("For BigQuery, data must be a pandas.DataFrame, dict, or list[dict].")

    def read(
            self,
            resource: str,
            *,
            doc_id: Optional[str] = None,
            query: Optional[str] = None,
            limit: int = 100,
        ) -> Any:
        """
        Read/fetch.

        - firebase: resource=collection, doc_id optional (single doc if provided, else list of docs)
        - bq: query optional (returns DataFrame). If query is omitted, reads table with LIMIT.
        """
        if self._active == "firebase":
            col = self.firestore.collection(resource)
            if doc_id is not None:
                doc = col.document(str(doc_id)).get()
                return doc.to_dict() if doc.exists else None
            return [d.to_dict() for d in col.limit(limit).stream()]

        sql = query or f"SELECT * FROM `{resource}` LIMIT {int(limit)}"
        return self.bq.query(sql).to_dataframe()

    def update(self, resource: str, identifier: str, data: dict[str, Any]) -> Any:
        """
        Update existing.

        - firebase: identifier=doc_id, data=dict fields
        - bq: identifier=WHERE clause (SQL), data=dict of columns to set
              Example: update("dw-fin.pif_project.players_table", "id_jogo='...'", {"rebuys": 2})
        """
        if self._active == "firebase":
            self.firestore.collection(resource).document(str(identifier)).update(self._firestore_prepare(data))
            return True

        where = identifier.strip()
        if not where:
            raise ValueError("BigQuery update requires a non-empty WHERE clause in identifier.")
        if not data:
            return True

        set_expr = ", ".join([f"`{k}` = @{k}" for k in data.keys()])
        sql = f"UPDATE `{resource}` SET {set_expr} WHERE {where}"
        params = [bigquery.ScalarQueryParameter(k, _bq_param_type(v), v) for k, v in data.items()]
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        job = self.bq.query(sql, job_config=job_config)
        job.result()
        return job.job_id

    def delete(self, resource: str, identifier: str) -> Any:
        """
        Delete.

        - firebase: identifier=doc_id
        - bq: identifier=WHERE clause (SQL)
        """
        if self._active == "firebase":
            self.firestore.collection(resource).document(str(identifier)).delete()
            return True

        where = identifier.strip()
        if not where:
            raise ValueError("BigQuery delete requires a non-empty WHERE clause in identifier.")
        sql = f"DELETE FROM `{resource}` WHERE {where}"
        job = self.bq.query(sql)
        job.result()
        return job.job_id

    # ---------- helpers ----------
    def _firestore_prepare(self, data: Any) -> Any:
        # Keep conversions local so callers don't need to import auxiliares.prepare_for_firestore
        import datetime as dt
        import numpy as np

        # sentinel
        if hasattr(firestore, "SERVER_TIMESTAMP") and data is firestore.SERVER_TIMESTAMP:
            return data
        if data is None:
            return None

        if isinstance(data, pd.DataFrame):
            return self._firestore_prepare(data.to_dict())
        if isinstance(data, pd.Series):
            return self._firestore_prepare(data.to_dict())

        if isinstance(data, dict):
            return {str(k).strip() or "_empty": self._firestore_prepare(v) for k, v in data.items()}
        if isinstance(data, (list, tuple)):
            return [self._firestore_prepare(i) for i in data]
        if hasattr(np, "ndarray") and isinstance(data, np.ndarray):
            return [self._firestore_prepare(i) for i in data.tolist()]

        if hasattr(np, "integer") and isinstance(data, np.integer):
            return int(data)
        if hasattr(np, "floating") and isinstance(data, np.floating):
            return None if np.isnan(data) else float(data)
        if hasattr(np, "bool_") and isinstance(data, np.bool_):
            return bool(data)

        try:
            if hasattr(pd, "NA") and data is pd.NA:
                return None
            if isinstance(data, float) and pd.isna(data):
                return None
        except Exception:
            pass

        if isinstance(data, (dt.datetime, dt.date)):
            return data.isoformat()

        if isinstance(data, (str, int, float, bool)):
            return data

        return str(data)


def _bq_param_type(v: Any) -> str:
    if isinstance(v, bool):
        return "BOOL"
    if isinstance(v, int) and not isinstance(v, bool):
        return "INT64"
    if isinstance(v, float):
        return "FLOAT64"
    return "STRING"

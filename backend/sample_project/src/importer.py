"""
Sample project — data importer.
Used by the bundled 'refactor-class' scenario.
"""
import csv
import io


class DataImporter:

    def __init__(self, source: str) -> None:
        self.source = source
        self._records: list[dict] = []

    def load(self, raw_csv: str) -> list[dict]:
        """Parse CSV and return list of records."""
        reader = csv.DictReader(io.StringIO(raw_csv))
        self._records = [row for row in reader]
        return self._records

    def validate(self, records: list[dict], required_fields: list[str]) -> bool:
        """Validate that all records contain required fields."""
        for record in records:
            for field in required_fields:
                if field not in record:
                    return False
        return True

    def transform(self, records: list[dict]) -> list[dict]:
        """Apply basic normalisation."""
        return [
            {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            for row in records
        ]

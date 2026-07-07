from dataclasses import dataclass
import psycopg


@dataclass(slots=True)
class SqlCapability:
    connection: psycopg.Connection

    def execute(self, sql: str):
        with self.connection.cursor() as cur:
            cur.execute(sql)

@dataclass(slots=True)
class DiffCapability:

    def create_diff(self):
        pass

@dataclass(slots=True)
class ExportCapability:

    def export(self):
        pass

@dataclass(slots=True)
class MailCapability:


    def send(
        self,
        receiver: str,
        subject: str,
        body: str,
    ):
        pass
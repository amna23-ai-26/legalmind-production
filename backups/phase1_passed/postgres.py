
import os
import psycopg2
from psycopg2.extras import Json


class PostgreSQLDatabase:
    """
    PostgreSQL storage layer for LegalMind Phase 1.

    Stores:
    - contract metadata
    - segmented clauses
    - hierarchical chunks
    - risk findings
    """

    def __init__(
        self,
        host=None,
        port=None,
        database=None,
        user=None,
        password=None
    ):
        self.host = host or os.getenv(
            "POSTGRES_HOST",
            "localhost"
        )

        self.port = port or os.getenv(
            "POSTGRES_PORT",
            "5432"
        )

        self.database = database or os.getenv(
            "POSTGRES_DB",
            "legalmind"
        )

        self.user = user or os.getenv(
            "POSTGRES_USER",
            "postgres"
        )

        self.password = password or os.getenv(
            "POSTGRES_PASSWORD",
            "legalmind123"
        )

    def connect(self):
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password
        )

    def create_tables(self):
        """
        Create the LegalMind Phase 1 relational schema.
        """

        conn = self.connect()

        try:
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS contracts (
                    id SERIAL PRIMARY KEY,
                    document_name TEXT NOT NULL,
                    contract_type TEXT,
                    agreement_date TEXT,
                    effective_date TEXT,
                    governing_law TEXT,
                    parties JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS clauses (
                    id SERIAL PRIMARY KEY,
                    contract_id INTEGER NOT NULL
                        REFERENCES contracts(id)
                        ON DELETE CASCADE,
                    clause_id INTEGER NOT NULL,
                    heading TEXT,
                    text TEXT NOT NULL,
                    character_count INTEGER,
                    word_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(contract_id, clause_id)
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS hierarchical_chunks (
                    id SERIAL PRIMARY KEY,
                    contract_id INTEGER NOT NULL
                        REFERENCES contracts(id)
                        ON DELETE CASCADE,
                    clause_id INTEGER,
                    chunk_id INTEGER NOT NULL,
                    heading TEXT,
                    text TEXT NOT NULL,
                    word_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(contract_id, chunk_id)
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS risk_findings (
                    id SERIAL PRIMARY KEY,
                    contract_id INTEGER NOT NULL
                        REFERENCES contracts(id)
                        ON DELETE CASCADE,
                    clause_id INTEGER,
                    risk_category TEXT,
                    risk_score FLOAT,
                    risk_level TEXT,
                    finding JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            conn.commit()

            return True

        finally:
            cur.close()
            conn.close()

    def insert_contract(self, metadata):
        """
        Insert contract metadata and return the contract ID.
        """

        conn = self.connect()

        try:
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO contracts (
                    document_name,
                    contract_type,
                    agreement_date,
                    effective_date,
                    governing_law,
                    parties
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                metadata.get("document_name"),
                metadata.get("contract_type"),
                metadata.get("agreement_date"),
                metadata.get("effective_date"),
                metadata.get("governing_law"),
                Json(metadata.get("parties", []))
            ))

            contract_id = cur.fetchone()[0]

            conn.commit()

            return contract_id

        finally:
            cur.close()
            conn.close()

    def insert_clauses(self, contract_id, clauses):
        """
        Insert segmented clauses for a contract.
        """

        conn = self.connect()

        try:
            cur = conn.cursor()

            inserted = 0

            for clause in clauses:

                cur.execute("""
                    INSERT INTO clauses (
                        contract_id,
                        clause_id,
                        heading,
                        text,
                        character_count,
                        word_count
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (
                        contract_id,
                        clause_id
                    )
                    DO UPDATE SET
                        heading = EXCLUDED.heading,
                        text = EXCLUDED.text,
                        character_count = EXCLUDED.character_count,
                        word_count = EXCLUDED.word_count;
                """, (
                    contract_id,
                    clause.get("clause_id"),
                    clause.get("heading"),
                    clause.get("text"),
                    clause.get(
                        "character_count",
                        len(clause.get("text", ""))
                    ),
                    clause.get(
                        "word_count",
                        len(
                            clause.get(
                                "text",
                                ""
                            ).split()
                        )
                    )
                ))

                inserted += 1

            conn.commit()

            return inserted

        finally:
            cur.close()
            conn.close()

    def insert_chunks(self, contract_id, chunks):
        """
        Insert hierarchical chunks for a contract.
        """

        conn = self.connect()

        try:
            cur = conn.cursor()

            inserted = 0

            for chunk in chunks:

                cur.execute("""
                    INSERT INTO hierarchical_chunks (
                        contract_id,
                        clause_id,
                        chunk_id,
                        heading,
                        text,
                        word_count
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (
                        contract_id,
                        chunk_id
                    )
                    DO UPDATE SET
                        clause_id = EXCLUDED.clause_id,
                        heading = EXCLUDED.heading,
                        text = EXCLUDED.text,
                        word_count = EXCLUDED.word_count;
                """, (
                    contract_id,
                    chunk.get("clause_id"),
                    chunk.get("chunk_id"),
                    chunk.get("heading"),
                    chunk.get("text"),
                    chunk.get(
                        "word_count",
                        len(
                            chunk.get(
                                "text",
                                ""
                            ).split()
                        )
                    )
                ))

                inserted += 1

            conn.commit()

            return inserted

        finally:
            cur.close()
            conn.close()

    def insert_risk_finding(
        self,
        contract_id,
        clause_id,
        risk_finding
    ):
        """
        Store one Risk Agent finding.
        """

        conn = self.connect()

        try:
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO risk_findings (
                    contract_id,
                    clause_id,
                    risk_category,
                    risk_score,
                    risk_level,
                    finding
                )
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (
                contract_id,
                clause_id,
                risk_finding.get("risk_category"),
                risk_finding.get("risk_score"),
                risk_finding.get("risk_level"),
                Json(risk_finding)
            ))

            conn.commit()

        finally:
            cur.close()
            conn.close()

    def count(self, table_name):
        """
        Return row count for a known LegalMind table.
        """

        allowed = {
            "contracts",
            "clauses",
            "hierarchical_chunks",
            "risk_findings"
        }

        if table_name not in allowed:
            raise ValueError(
                f"Unsupported table: {table_name}"
            )

        conn = self.connect()

        try:
            cur = conn.cursor()

            cur.execute(
                f"SELECT COUNT(*) FROM {table_name};"
            )

            return cur.fetchone()[0]

        finally:
            cur.close()
            conn.close()

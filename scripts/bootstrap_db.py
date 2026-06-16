from server.db.bootstrap import bootstrapper
from server.db.session import SessionLocal
from server.services.ingestion import ingestion_service


def main() -> None:
    bootstrapper.bootstrap()
    with SessionLocal() as db:
        if not ingestion_service.has_knowledge(db):
            ingestion_service.ingest(db)


if __name__ == "__main__":
    main()

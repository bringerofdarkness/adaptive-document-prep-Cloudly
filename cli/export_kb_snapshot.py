import typer

from app.db.models import PrepSession
from app.db.session import SessionLocal
from app.services.snapshot_service import save_and_export_kb_snapshot


def main(
    output_path: str = typer.Option(
        "outputs/kb_snapshot_latest.json",
        help="Where to write the KB snapshot JSON.",
    ),
) -> None:
    db = SessionLocal()

    try:
        latest_session = (
            db.query(PrepSession)
            .order_by(PrepSession.created_at.desc())
            .first()
        )

        if latest_session is None:
            raise typer.BadParameter("No prep session found.")

        snapshot = save_and_export_kb_snapshot(
            db=db,
            current_session_id=latest_session.id,
            output_path=output_path,
        )

        typer.echo(f"Snapshot exported: {output_path}")
        typer.echo(f"Current session: {snapshot['current_session_id']}")
        typer.echo(f"Recent sessions included: {snapshot['recent_session_count']}")

    finally:
        db.close()


if __name__ == "__main__":
    typer.run(main)
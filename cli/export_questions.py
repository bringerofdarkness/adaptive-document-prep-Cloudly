import typer

from app.db.models import PrepSession
from app.db.session import SessionLocal
from app.services.question_export_service import export_session_questions


def main(
    output_path: str = typer.Option(
        "outputs/questions_latest.json",
        help="Where to write the questions JSON.",
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

        payload = export_session_questions(
            db=db,
            session_id=latest_session.id,
            output_path=output_path,
        )

        typer.echo(f"Questions exported: {output_path}")
        typer.echo(f"Session: {payload['session_id']}")
        typer.echo(f"Questions: {len(payload['questions'])}")

    finally:
        db.close()


if __name__ == "__main__":
    typer.run(main)
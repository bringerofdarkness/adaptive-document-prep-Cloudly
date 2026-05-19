from pathlib import Path

import typer

from app.db.repositories.document_repo import get_latest_document
from app.db.repositories.session_repo import clear_prep_history_for_document
from app.db.session import SessionLocal
from app.services.prep_service import run_prep_session
from app.services.question_export_service import export_session_questions
from app.services.snapshot_service import save_and_export_kb_snapshot


DEFAULT_SCENARIO_A_SECTIONS = [3, 7]


def main(
    questions_per_section: int = typer.Option(2),
    output_root: str = typer.Option("outputs"),
) -> None:
    db = SessionLocal()

    try:
        document = get_latest_document(db)

        if document is None:
            raise typer.BadParameter("No document found. Run ingestion first.")

        clear_prep_history_for_document(
            db=db,
            document_id=document.id,
        )

        result = run_prep_session(
            db=db,
            selected_section_numbers=DEFAULT_SCENARIO_A_SECTIONS,
            questions_per_section=questions_per_section,
            simulation_strategy="alternating",
        )

        output_dir = Path(output_root) / "scenario_a"

        export_session_questions(
            db=db,
            session_id=result["session_id"],
            output_path=output_dir / "questions_scenario_a.json",
        )

        save_and_export_kb_snapshot(
            db=db,
            current_session_id=result["session_id"],
            output_path=output_dir / "kb_snapshot_scenario_a.json",
        )

        typer.echo(
            f"Scenario A complete | session={result['session_id']} | "
            f"mode={result['mode']} | score={result['score']}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    typer.run(main)
from pathlib import Path

import typer

from app.db.repositories.document_repo import get_latest_document
from app.db.repositories.session_repo import clear_prep_history_for_document
from app.db.session import SessionLocal
from app.services.prep_service import run_prep_session
from app.services.question_export_service import export_session_questions
from app.services.snapshot_service import save_and_export_kb_snapshot


SCENARIO_B_RUNS = [
    {"iteration": 1, "sections": [5, 8], "simulation_strategy": "section8_weak"},
    {"iteration": 2, "sections": [6, 8, 9], "simulation_strategy": "section8_weak"},
    {"iteration": 3, "sections": [8], "simulation_strategy": "section8_weak"},
]


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

        for run_config in SCENARIO_B_RUNS:
            iteration = run_config["iteration"]
            output_dir = Path(output_root) / f"scenario_b_iter{iteration}"

            result = run_prep_session(
                
                db=db,
                selected_section_numbers=run_config["sections"],
                questions_per_section=questions_per_section,
                simulation_strategy=run_config["simulation_strategy"],
            )

            export_session_questions(
                db=db,
                session_id=result["session_id"],
                output_path=output_dir / f"questions_iter{iteration}.json",
            )

            save_and_export_kb_snapshot(
                db=db,
                current_session_id=result["session_id"],
                output_path=output_dir / f"kb_snapshot_iter{iteration}.json",
            )

            typer.echo(
                f"Scenario B iteration {iteration} complete | "
                f"session={result['session_id']} | "
                f"mode={result['mode']} | "
                f"score={result['score']}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    typer.run(main)

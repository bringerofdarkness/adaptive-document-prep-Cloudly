import typer

from app.db.session import SessionLocal
from app.services.prep_service import run_mock_prep_session


def parse_sections(raw_sections: str) -> list[int]:
    return [
        int(item.strip())
        for item in raw_sections.split(",")
        if item.strip()
    ]


def main(
    sections: str = typer.Option(..., help="Comma-separated section numbers, e.g. 5,8"),
    questions_per_section: int = typer.Option(2),
    simulation_strategy: str = typer.Option("section8_weak"),
) -> None:
    selected_section_numbers = parse_sections(sections)

    db = SessionLocal()

    try:
        result = run_mock_prep_session(
            db=db,
            selected_section_numbers=selected_section_numbers,
            questions_per_section=questions_per_section,
            simulation_strategy=simulation_strategy,
        )

        typer.echo("Prep session saved.")
        typer.echo(result)

    finally:
        db.close()


if __name__ == "__main__":
    typer.run(main)
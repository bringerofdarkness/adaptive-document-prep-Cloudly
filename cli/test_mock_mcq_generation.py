import typer

from app.db.repositories.document_repo import get_latest_document
from app.db.session import SessionLocal
from app.llm.mcq_generator import generate_mock_mcqs
from app.retrieval.retriever import retrieve_chunks_for_sections


app = typer.Typer(help="Test mock MCQ generation from retrieved chunks.")


def parse_sections(raw_sections: str) -> list[int]:
    return [
        int(item.strip())
        for item in raw_sections.split(",")
        if item.strip()
    ]


@app.command()
def run(
    sections: str = typer.Option(..., help="Comma-separated section numbers, e.g. 5,8"),
    questions_per_section: int = typer.Option(2),
) -> None:
    selected_section_numbers = parse_sections(sections)

    db = SessionLocal()

    try:
        document = get_latest_document(db)

        if document is None:
            raise typer.BadParameter("No document found. Run ingestion first.")

        retrieved_chunks = retrieve_chunks_for_sections(
            db=db,
            document=document,
            selected_section_numbers=selected_section_numbers,
            query="Generate MCQs from selected sections.",
            limit=12,
        )

        mcq_set = generate_mock_mcqs(
            retrieved_chunks=retrieved_chunks,
            selected_section_numbers=selected_section_numbers,
            questions_per_section=questions_per_section,
        )

        typer.echo(f"Generated questions: {len(mcq_set.questions)}")

        for question in mcq_set.questions:
            typer.echo(
                f"{question.section_number} | {question.topic} | "
                f"answer={question.correct_answer} | {question.adaptation_reason}"
            )

        typer.echo("Mock MCQ generation passed.")

    finally:
        db.close()


if __name__ == "__main__":
    app()
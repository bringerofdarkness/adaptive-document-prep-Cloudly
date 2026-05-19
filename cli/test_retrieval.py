import typer

from app.db.repositories.document_repo import get_latest_document
from app.db.session import SessionLocal
from app.retrieval.retriever import retrieve_chunks_for_sections


app = typer.Typer(help="Test deterministic section-filtered retrieval.")


def parse_sections(raw_sections: str) -> list[int]:
    return [
        int(item.strip())
        for item in raw_sections.split(",")
        if item.strip()
    ]


@app.command()
def run(
    sections: str = typer.Option(..., help="Comma-separated section numbers, e.g. 5,8"),
    query: str = typer.Option("Generate study questions from the selected sections."),
    limit: int = typer.Option(8),
) -> None:
    selected_section_numbers = parse_sections(sections)

    db = SessionLocal()

    try:
        document = get_latest_document(db)

        if document is None:
            raise typer.BadParameter("No document found. Run ingestion first.")

        chunks = retrieve_chunks_for_sections(
            db=db,
            document=document,
            selected_section_numbers=selected_section_numbers,
            query=query,
            limit=limit,
        )

        typer.echo(f"Selected sections: {selected_section_numbers}")
        typer.echo(f"Retrieved chunks: {len(chunks)}")
        typer.echo("")

        for chunk in chunks:
            typer.echo(
                "chunk_id={chunk_id} | section={section_number} | "
                "chunk_index={chunk_index} | page={page_number} | score={score:.4f}".format(
                    **chunk
                )
            )

        retrieved_sections = sorted({chunk["section_number"] for chunk in chunks})
        typer.echo("")
        typer.echo(f"Retrieved section numbers only: {retrieved_sections}")

        invalid_sections = [
            section_number
            for section_number in retrieved_sections
            if section_number not in selected_section_numbers
        ]

        if invalid_sections:
            raise RuntimeError(f"Out-of-section retrieval detected: {invalid_sections}")

        typer.echo("Strict section filtering passed.")

    finally:
        db.close()


if __name__ == "__main__":
    app()
import typer

from app.db.session import Base, engine
from app.db import models  # noqa: F401


app = typer.Typer(help="Database utility commands.")


@app.command()
def reset() -> None:
    """Drop and recreate all PostgreSQL tables."""
    typer.echo("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)

    typer.echo("Creating tables...")
    Base.metadata.create_all(bind=engine)

    typer.echo("Database reset complete.")


@app.command()
def create() -> None:
    """Create tables without dropping existing data."""
    typer.echo("Creating tables if missing...")
    Base.metadata.create_all(bind=engine)

    typer.echo("Database tables are ready.")


if __name__ == "__main__":
    app()

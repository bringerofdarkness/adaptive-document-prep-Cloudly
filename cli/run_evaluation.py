import typer

from cli.run_scenario_a import main as run_scenario_a
from cli.run_scenario_b import main as run_scenario_b


def main(
    questions_per_section: int = typer.Option(2),
) -> None:
    typer.echo("Running Scenario A...")
    run_scenario_a(
        questions_per_section=questions_per_section,
        output_root="outputs",
    )

    typer.echo("Running Scenario B...")
    run_scenario_b(
        questions_per_section=questions_per_section,
        output_root="outputs",
    )

    typer.echo("Evaluation complete. Outputs are available under the outputs directory.")


if __name__ == "__main__":
    typer.run(main)
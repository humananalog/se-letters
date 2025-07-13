"""Command-line interface for the SE Letters project."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .core.config import get_config, reset_config
from .core.pipeline import Pipeline
from .core.exceptions import SELettersError
from .utils.logger import setup_logging

console = Console()


@click.group()
@click.version_option()
def cli() -> None:
    """SE Letters - Schneider Electric Obsolescence Letter Matching."""
    pass


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def run(config: Optional[Path], verbose: bool) -> None:
    """Run the complete SE Letters pipeline."""
    try:
        # Setup logging
        setup_logging(verbose=verbose)
        
        # Load configuration
        if config:
            reset_config()  # Reset to load new config
        app_config = get_config(config)
        
        console.print("[bold green]Starting SE Letters Pipeline[/bold green]")
        console.print(f"Configuration: {config or 'config/config.yaml'}")
        
        # Run pipeline
        asyncio.run(_run_pipeline(app_config))
        
    except SELettersError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        sys.exit(1)


async def _run_pipeline(config) -> None:
    """Run the pipeline with progress tracking."""
    pipeline = Pipeline(config)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running pipeline...", total=None)
            
            # Run the pipeline
            results = await pipeline.run()
            
            progress.update(task, description="Pipeline completed!")
            
        # Display results
        console.print("\n[bold green]Pipeline Results:[/bold green]")
        console.print(f"Status: {results['status']}")
        console.print(f"Documents processed: {results['total_documents']}")
        console.print(f"Letters processed: {results['total_letters']}")
        console.print(f"Records matched: {results['matched_records']}")
        console.print(f"Records unmatched: {results['unmatched_records']}")
        console.print(f"Processing time: {results['processing_time']:.2f}s")
        
        console.print("\n[bold green]Output Files:[/bold green]")
        for file_type, file_path in results['output_files'].items():
            console.print(f"{file_type}: {file_path}")
            
    finally:
        await pipeline.cleanup()


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
def validate_config(config: Optional[Path]) -> None:
    """Validate the configuration file."""
    try:
        if config:
            reset_config()
        app_config = get_config(config)
        console.print("[bold green]Configuration is valid![/bold green]")
        
        # Display key settings
        console.print("\n[bold]Key Settings:[/bold]")
        console.print(f"API Model: {app_config.api.model}")
        console.print(f"Input Directory: {app_config.data.letters_directory}")
        console.print(f"Excel File: {app_config.data.excel_file}")
        console.print(f"Output Directory: {app_config.data.json_directory}")
        console.print(f"Batch Size: {app_config.processing.batch_size}")
        console.print(f"Max Workers: {app_config.processing.max_workers}")
        
    except SELettersError as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("input_dir", type=click.Path(exists=True, path_type=Path))
def scan(input_dir: Path) -> None:
    """Scan input directory for supported files."""
    supported_formats = [".pdf", ".docx", ".doc"]
    
    console.print(f"[bold]Scanning directory:[/bold] {input_dir}")
    
    files_found = {}
    total_files = 0
    
    for ext in supported_formats:
        files = list(input_dir.glob(f"*{ext}"))
        files_found[ext] = files
        total_files += len(files)
        
        if files:
            console.print(f"\n[bold green]{ext.upper()} files ({len(files)}):[/bold green]")
            for file in files:
                console.print(f"  - {file.name}")
    
    if total_files == 0:
        console.print("[bold red]No supported files found![/bold red]")
        console.print(f"Supported formats: {', '.join(supported_formats)}")
    else:
        console.print(f"\n[bold green]Total files found: {total_files}[/bold green]")


@cli.command()
@click.argument("json_dir", type=click.Path(exists=True, path_type=Path))
def report(json_dir: Path) -> None:
    """Generate a report from processed JSON files."""
    from .models.letter import Letter
    
    json_files = list(json_dir.glob("*.json"))
    
    if not json_files:
        console.print("[bold red]No JSON files found![/bold red]")
        return
    
    console.print(f"[bold]Processing {len(json_files)} JSON files...[/bold]")
    
    letters = []
    for json_file in json_files:
        try:
            letter = Letter.from_json(json_file)
            letters.append(letter)
        except Exception as e:
            console.print(f"[bold red]Error loading {json_file}:[/bold red] {e}")
    
    if not letters:
        console.print("[bold red]No valid letters found![/bold red]")
        return
    
    # Generate report
    console.print(f"\n[bold green]Report Summary:[/bold green]")
    console.print(f"Total letters: {len(letters)}")
    
    # Range statistics
    all_ranges = []
    for letter in letters:
        all_ranges.extend(letter.ranges)
    
    unique_ranges = set(all_ranges)
    console.print(f"Unique ranges detected: {len(unique_ranges)}")
    
    # Confidence statistics
    high_confidence = sum(1 for letter in letters if letter.metadata.is_high_confidence)
    console.print(f"High confidence letters: {high_confidence}/{len(letters)}")
    
    # Modernization paths
    with_modernization = sum(1 for letter in letters if letter.metadata.has_modernization_path)
    console.print(f"Letters with modernization paths: {with_modernization}/{len(letters)}")


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main() 
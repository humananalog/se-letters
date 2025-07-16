 """Command-line interface for the SE Letters project."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .core.config import get_config
from .services.production_pipeline_service import ProductionPipelineService
from .core.exceptions import SELettersError
from .utils.logger import setup_logging

console = Console()
app = typer.Typer()


@app.callback()
def main():
    """SE Letters - Schneider Electric Obsolescence Letter Matching."""
    pass


@app.command()
def run(
    config: Optional[Path] = typer.Option(
        None,
    "--config",
    "-c",
    help="Path to configuration file",
    ),
    verbose: bool = typer.Option(
        False,
    "--verbose",
    "-v",
    help="Enable verbose logging",
    ),
) -> None:
    """Run the SE Letters pipeline."""
    
    try:
        # Setup logging
        log_level = "DEBUG" if verbose else "INFO"
        setup_logging(level=log_level)
        
        # Load configuration
        if config:
            # Config loading from path - implementation needed
            pass 
        get_config(config)
        
        # Run pipeline
        console.print(
            "[bold green]Starting SE Letters Pipeline...[/bold green]")
        pipeline_service = ProductionPipelineService()
        
        # For CLI, we could process a test document or directory
        test_doc = Path("data/test/documents/PIX2B_Phase_out_Letter.pdf")
        if test_doc.exists():
            console.print(f"Processing test document: {test_doc}")
            result = pipeline_service.process_document(test_doc)
            console.print(f"✅ Processing completed: {result.success}")
        else:
            console.print("❌ No test document found")
        
    except SELettersError as e:
        console.print(f"[bold red]SE Letters error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        sys.exit(1)


@app.command()
def validate(
    config: Optional[Path] = typer.Option(
        None,
    "--config",
    "-c",
    help="Path to configuration file",
    ),
) -> None:
    """Validate configuration and dependencies."""
    
    try:
        if config:
            # Config loading from path - implementation needed
            pass
        app_config = get_config(config)
        console.print("[bold green]Configuration is valid![/bold green]")
        
        console.print("\n[bold]Key Settings:[/bold]")
        console.print(f"API Model: {app_config.api.model}")
        console.print(f"Input Directory: {app_config.data.letters_directory}")
        console.print(
            f"Product Database: {app_config.data.database.product_database}")
        console.print(
            f"Letter Database: {app_config.data.database.letter_database}")
        console.print(f"Output Directory: {app_config.data.json_directory}")
        console.print(f"Batch Size: {app_config.processing.batch_size}")
        
    except Exception as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        sys.exit(1)


@app.command()
def scan(input_dir: Path) -> None:
    """Scan input directory for supported files."""
    try:
        config = get_config()
        supported_formats = config.data.supported_formats
    
    console.print(f"[bold]Scanning directory:[/bold] {input_dir}")
    
        files = []
        for format_ext in supported_formats:
            files.extend(input_dir.glob(f"*{format_ext}"))
        
        if files:
            console.print(f"\n[bold green]Found {len(files)} files:[/bold green]")
            for file in sorted(files):
                size_mb = file.stat().st_size / (1024 * 1024)
                console.print(f"  {file.name} ({size_mb:.1f} MB)")
    else:
            console.print("[bold yellow]No supported files found.[/bold yellow]")
            
    except Exception as e:
        console.print(f"[bold red]Scan error:[/bold red] {e}")
        sys.exit(1)


@app.command()
def report(json_dir: Path) -> None:
    """Generate a report from processed JSON files."""
    try:
    json_files = list(json_dir.glob("*.json"))
    
    if not json_files:
            console.print("[bold yellow]No JSON files found.[/bold yellow]")
        return
    
        console.print(f"[bold]Processing Report:[/bold]")
        console.print(f"Found {len(json_files)} JSON files")
        
        # Simple report implementation
        for json_file in sorted(json_files):
            console.print(f"  {json_file.name}")
            
        except Exception as e:
        console.print(f"[bold red]Report error:[/bold red] {e}")
        sys.exit(1)


def cli():
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    cli() 
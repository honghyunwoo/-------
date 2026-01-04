"""
StoicFlow CLI - Main entry point.

Usage:
    stoicflow generate           # Generate new script
    stoicflow compose 1          # Compose video from script #1
    stoicflow scripts list       # List available scripts
    stoicflow record 1           # Show recording guide for script #1
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from stoicflow.config.settings import settings

app = typer.Typer(
    name="stoicflow",
    help="YouTube Shorts automation for Stoic philosophy content",
    add_completion=False,
)
console = Console()

# Sub-commands
scripts_app = typer.Typer(help="Manage scripts")
app.add_typer(scripts_app, name="scripts")


def _load_scripts() -> list[dict]:
    """Load scripts from JSON file."""
    scripts_file = settings.scripts_dir / "stoic_premium.json"
    if scripts_file.exists():
        with open(scripts_file) as f:
            data = json.load(f)
            # Handle both formats: list or dict with 'scripts' key
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "scripts" in data:
                return data["scripts"]
            return []
    return []


def _save_scripts(scripts: list[dict]) -> None:
    """Save scripts to JSON file."""
    settings.ensure_directories()
    scripts_file = settings.scripts_dir / "stoic_premium.json"
    with open(scripts_file, "w", encoding="utf-8") as f:
        json.dump(scripts, f, ensure_ascii=False, indent=2)


@app.command()
def generate(
    topic: Optional[str] = typer.Option(None, "--topic", "-t", help="Topic to focus on"),
    quote: Optional[str] = typer.Option(None, "--quote", "-q", help="Specific quote to use"),
    author: Optional[str] = typer.Option(None, "--author", "-a", help="Quote author"),
):
    """Generate a new script using AI."""
    console.print("[bold blue]Generating script...[/]")

    async def _generate():
        from stoicflow.infrastructure.llm.claude_adapter import ClaudeAdapter

        llm = ClaudeAdapter()
        script = await llm.generate_script(topic=topic, quote=quote, author=author)

        # Save to scripts
        scripts = _load_scripts()
        script_dict = {
            "id": script.id,
            "quote": script.quote,
            "author": script.author,
            "theme": script.theme,
            "script": {
                "hook": script.hook,
                "quote_read": script.quote_read,
                "explanation": script.explanation,
                "cta": script.cta,
            },
            "tts_text": script.tts_text,
            "duration_estimate": script.duration_estimate,
        }
        scripts.append(script_dict)
        _save_scripts(scripts)

        return script

    try:
        script = asyncio.run(_generate())

        console.print(Panel(
            f"[bold]{script.quote}[/]\n\n"
            f"- {script.author}",
            title=f"Script #{script.id}",
            border_style="green",
        ))

        console.print("\n[bold]Hook:[/]", script.hook)
        console.print("[bold]Quote:[/]", script.quote_read)
        console.print("[bold]Explanation:[/]", script.explanation)
        console.print("[bold]CTA:[/]", script.cta)

        console.print(f"\n[green]Script saved! Use 'stoicflow record {script.id}' for recording guide.[/]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)


@app.command()
def compose(
    script_id: int = typer.Argument(..., help="Script ID to compose"),
    audio: Optional[Path] = typer.Option(None, "--audio", "-a", help="Path to recorded audio"),
    background: Optional[Path] = typer.Option(None, "--bg", "-b", help="Background video/image"),
    music: Optional[Path] = typer.Option(None, "--music", "-m", help="Background music"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output path"),
    with_tts: bool = typer.Option(False, "--with-tts", help="Use TTS instead of manual recording"),
):
    """Compose video from a script."""
    scripts = _load_scripts()
    script_data = next((s for s in scripts if s["id"] == script_id), None)

    if not script_data:
        console.print(f"[red]Script #{script_id} not found[/]")
        raise typer.Exit(1)

    if not audio and not with_tts:
        console.print("[yellow]No audio provided. Use --audio or --with-tts[/]")
        console.print(f"[dim]Run 'stoicflow record {script_id}' for recording guide[/]")
        raise typer.Exit(1)

    console.print(f"[bold blue]Composing video for script #{script_id}...[/]")

    async def _compose():
        from stoicflow.application.interfaces.tts_provider import SkipTTSProvider
        from stoicflow.application.services.pipeline import Pipeline
        from stoicflow.domain.entities.script import Script
        from stoicflow.infrastructure.llm.claude_adapter import ClaudeAdapter
        from stoicflow.infrastructure.tts.edge_tts_adapter import EdgeTTSAdapter
        from stoicflow.infrastructure.video.moviepy_adapter import MoviePyAdapter

        # Initialize adapters
        llm = ClaudeAdapter()
        tts = EdgeTTSAdapter() if with_tts else SkipTTSProvider()
        editor = MoviePyAdapter()

        pipeline = Pipeline(llm=llm, tts=tts, editor=editor)

        # Convert to Script entity
        script = Script.from_json(script_data)

        result = await pipeline.run(
            script=script,
            audio_path=audio,
            background_path=background,
            music_path=music,
        )

        return result

    try:
        result = asyncio.run(_compose())

        if result.success and result.video:
            console.print(f"[green]Video created: {result.video.video_path}[/]")
            console.print(f"[dim]Duration: {result.video.duration:.1f}s[/]")
        else:
            console.print(f"[red]Failed: {result.error}[/]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)


@app.command()
def record(script_id: int = typer.Argument(..., help="Script ID")):
    """Show recording guide for a script."""
    scripts = _load_scripts()
    script_data = next((s for s in scripts if s["id"] == script_id), None)

    if not script_data:
        console.print(f"[red]Script #{script_id} not found[/]")
        raise typer.Exit(1)

    from stoicflow.domain.entities.script import Script

    script = Script.from_json(script_data)
    guide = script.to_recording_guide()

    console.print(Panel(guide, title="Recording Guide", border_style="blue"))


@scripts_app.command("list")
def list_scripts():
    """List all available scripts."""
    scripts = _load_scripts()

    if not scripts:
        console.print("[yellow]No scripts found. Run 'stoicflow generate' to create one.[/]")
        return

    table = Table(title="Available Scripts")
    table.add_column("ID", style="cyan")
    table.add_column("Author", style="green")
    table.add_column("Quote (preview)")
    table.add_column("Used", style="dim")

    for s in scripts:
        quote_preview = s["quote"][:40] + "..." if len(s["quote"]) > 40 else s["quote"]
        used = s.get("used_count", 0)
        table.add_row(str(s["id"]), s["author"], quote_preview, str(used))

    console.print(table)


@scripts_app.command("show")
def show_script(script_id: int = typer.Argument(..., help="Script ID")):
    """Show script details."""
    scripts = _load_scripts()
    script_data = next((s for s in scripts if s["id"] == script_id), None)

    if not script_data:
        console.print(f"[red]Script #{script_id} not found[/]")
        raise typer.Exit(1)

    script = script_data["script"]

    console.print(Panel(
        f"[bold]{script_data['quote']}[/]\n\n"
        f"[dim]- {script_data['author']}[/]",
        title=f"Script #{script_id}",
        border_style="blue",
    ))

    console.print("\n[bold yellow]Hook:[/]")
    console.print(f"  {script['hook']}")

    console.print("\n[bold yellow]Quote Read:[/]")
    console.print(f"  {script['quote_read']}")

    console.print("\n[bold yellow]Explanation:[/]")
    console.print(f"  {script['explanation']}")

    console.print("\n[bold yellow]CTA:[/]")
    console.print(f"  {script['cta']}")


@app.command()
def upload(
    video_path: Path = typer.Argument(..., help="Video file to upload"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Video title"),
    privacy: str = typer.Option("private", "--privacy", "-p", help="Privacy: public, private, unlisted"),
):
    """Upload video to YouTube."""
    if not video_path.exists():
        console.print(f"[red]Video not found: {video_path}[/]")
        raise typer.Exit(1)

    console.print(f"[bold blue]Uploading {video_path}...[/]")

    async def _upload():
        from stoicflow.domain.entities.video import Video
        from stoicflow.infrastructure.youtube.youtube_api_adapter import YouTubeAPIAdapter

        publisher = YouTubeAPIAdapter()

        if not await publisher.authenticate():
            console.print("[red]YouTube authentication failed[/]")
            return None

        video = Video(
            id="upload",
            script_id=0,
            title=title or video_path.stem,
            description="",
            video_path=video_path,
        )

        async for update in publisher.publish_with_progress(video, privacy=privacy):
            from stoicflow.application.interfaces.publisher import PublishResult, UploadProgress

            if isinstance(update, UploadProgress):
                console.print(f"[dim]Uploading: {update.percentage:.1f}%[/]", end="\r")
            elif isinstance(update, PublishResult):
                return update

        return None

    try:
        result = asyncio.run(_upload())

        if result and result.success:
            console.print(f"\n[green]Uploaded successfully![/]")
            console.print(f"[bold]URL: {result.video_url}[/]")
        else:
            error = result.error if result else "Unknown error"
            console.print(f"\n[red]Upload failed: {error}[/]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)


@app.command()
def init():
    """Initialize StoicFlow project directories."""
    settings.ensure_directories()
    console.print("[green]Directories created:[/]")
    console.print(f"  - {settings.scripts_dir}")
    console.print(f"  - {settings.media_dir}")
    console.print(f"  - {settings.output_dir}")
    console.print(f"  - {settings.tokens_dir}")

    # Copy premium scripts from shorts-factory if available
    source = Path("/home/user/-------/shorts-factory/templates/stoic/scripts_premium.json")
    dest = settings.scripts_dir / "stoic_premium.json"

    if source.exists() and not dest.exists():
        import shutil
        shutil.copy(source, dest)
        console.print(f"  - Copied premium scripts to {dest}")

    console.print("\n[bold]Next steps:[/]")
    console.print("  1. Set ANTHROPIC_API_KEY in .env")
    console.print("  2. Run 'stoicflow scripts list' to see scripts")
    console.print("  3. Run 'stoicflow record <id>' for recording guide")


@app.callback()
def main():
    """StoicFlow - YouTube Shorts Automation Pipeline."""
    pass


if __name__ == "__main__":
    app()

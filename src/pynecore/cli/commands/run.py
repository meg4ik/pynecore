from pathlib import Path
from datetime import datetime
import queue
import threading
import time
import sys

from typer import Option, Argument, secho, Exit
from rich.progress import (Progress, SpinnerColumn, TextColumn, BarColumn,
                           ProgressColumn, Task)
from rich.text import Text

from ..app import app, app_state

from ...utils.rich.date_column import DateColumn
from pynecore.core.ohlcv_file import OHLCVReader

from pynecore.core.syminfo import SymInfo
from pynecore.core.script_runner import ScriptRunner

__all__ = []


class CustomTimeElapsedColumn(ProgressColumn):
    """Custom time elapsed column showing milliseconds."""

    def render(self, task: Task) -> Text:
        """Render the time elapsed with milliseconds."""
        elapsed = task.elapsed
        if elapsed is None:
            return Text("--:--.-", style="cyan")

        minutes = int(elapsed // 60)
        seconds = elapsed % 60

        return Text(f"{minutes:02d}:{seconds:06.3f}", style="cyan")


class CustomTimeRemainingColumn(ProgressColumn):
    """Custom time remaining column showing milliseconds."""

    def render(self, task: Task) -> Text:
        """Render the time remaining with milliseconds."""
        remaining = task.time_remaining
        if remaining is None:
            return Text("--:--.-", style="cyan")

        minutes = int(remaining // 60)
        seconds = remaining % 60

        return Text(f"{minutes:02d}:{seconds:06.3f}", style="cyan")


@app.command()
def run(
        script: Path = Argument(..., dir_okay=False, file_okay=True, help="Script to run"),
        data: Path = Argument(..., dir_okay=False, file_okay=True,
                              help="Data file to use (*.ohlcv)"),
        time_from: datetime | None = Option(None, '--from', '-f',
                                            formats=["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"],
                                            help="Start date (UTC), if not specified, will use the "
                                                 "first date in the data"),
        time_to: datetime | None = Option(None, '--to', '-t',
                                          formats=["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"],
                                          help="End date (UTC), if not specified, will use the last "
                                               "date in the data"),
        plot_path: Path | None = Option(None, "--plot", "-pp",
                                        help="Path to save the plot data",
                                        rich_help_panel="Out Path Options"),
        strat_path: Path | None = Option(None, "--strat", "-sp",
                                         help="Path to save the strategy statistics",
                                         rich_help_panel="Out Path Options"
                                         ),
        equity_path: Path | None = Option(None, "--equity", "-ep",
                                          help="Path to save the equity curve",
                                          rich_help_panel="Out Path Options"),
):
    """
    Run a script

    The system automatically searches for the workdir folder in the current and parent directories.
    If not found, it creates or uses a workdir folder in the current directory.

    If [bold]script[/] path is a name without full path, it will be searched in the [italic]"workdir/scripts"[/] directory.
    Similarly, if [bold]data[/] path is a name without full path, it will be searched in the [italic]"workdir/data"[/] directory.
    The [bold]plot_path[/], [bold]strat_path[/], and [bold]equity_path[/] work the same way - if they are names without full paths,
    they will be saved in the [italic]"workdir/output"[/] directory.
    """  # noqa
    # Ensure .py extension
    if script.suffix != ".py":
        script = script.with_suffix(".py")
    # Expand script path
    if len(script.parts) == 1:
        script = app_state.scripts_dir / script
    # Check if script exists
    if not script.exists():
        secho(f"Script file '{script}' not found!", fg="red", err=True)
        raise Exit(1)

    # Check file format and extension
    if data.suffix == "":
        # No extension, add .ohlcv
        data = data.with_suffix(".ohlcv")
    elif data.suffix != ".ohlcv":
        # Has extension but not .ohlcv
        secho(f"Cannot run with '{data.suffix}' files. The PyneCore runtime requires .ohlcv format.",
              fg="red", err=True)
        secho("If you're trying to use a different data format, please convert it first:", fg="red")
        symbol_placeholder = "YOUR_SYMBOL"
        timeframe_placeholder = "YOUR_TIMEFRAME"
        secho(f"pyne data convert-from {data} --symbol {symbol_placeholder} --timeframe {timeframe_placeholder}",
              fg="yellow")
        raise Exit(1)

    # Expand data path
    if len(data.parts) == 1:
        data = app_state.data_dir / data
    # Check if data exists
    if not data.exists():
        secho(f"Data file '{data}' not found!", fg="red", err=True)
        raise Exit(1)

    # Ensure .csv extension for plot path
    if plot_path and plot_path.suffix != ".csv":
        plot_path = plot_path.with_suffix(".csv")
    if not plot_path:
        plot_path = app_state.output_dir / f"{script.stem}.csv"

    # Ensure .csv extension for strategy path
    if strat_path and strat_path.suffix != ".csv":
        strat_path = strat_path.with_suffix(".csv")
    if not strat_path:
        strat_path = app_state.output_dir / f"{script.stem}_strat.csv"

    # Ensure .csv extension for equity path
    if equity_path and equity_path.suffix != ".csv":
        equity_path = equity_path.with_suffix(".csv")
    if not equity_path:
        equity_path = app_state.output_dir / f"{script.stem}_equity.csv"

    # Get symbol info for the data
    try:
        syminfo = SymInfo.load_toml(data.with_suffix(".toml"))
    except FileNotFoundError:
        secho(f"Symbol info file '{data.with_suffix('.toml')}' not found!", fg="red", err=True)
        raise Exit(1)

    # Open data file
    with OHLCVReader(data) as reader:
        if not time_from:
            time_from = reader.start_datetime
        if not time_to:
            time_to = reader.end_datetime
        time_from = time_from.replace(tzinfo=None)
        time_to = time_to.replace(tzinfo=None)

        total_seconds = int((time_to - time_from).total_seconds())

        # Get the iterator
        size = reader.get_size(int(time_from.timestamp()), int(time_to.timestamp()))
        ohlcv_iter = reader.read_from(int(time_from.timestamp()), int(time_to.timestamp()))

        # Add lib directory to Python path for library imports
        lib_dir = app_state.scripts_dir / "lib"
        lib_path_added = False
        if lib_dir.exists() and lib_dir.is_dir():
            sys.path.insert(0, str(lib_dir))
            lib_path_added = True

        # Show loading spinner while importing
        with Progress(
                SpinnerColumn(finished_text="[green]✓"),
                TextColumn("{task.description}"),
        ) as loading_progress:
            loading_task = loading_progress.add_task("Loading PyneCore...", total=1)

            try:
                # Create script runner (this is where the import happens)
                runner = ScriptRunner(script, ohlcv_iter, syminfo, last_bar_index=size - 1,
                                      plot_path=plot_path, strat_path=strat_path, equity_path=equity_path)
            finally:
                # Remove lib directory from Python path
                if lib_path_added:
                    sys.path.remove(str(lib_dir))

            # Mark as completed
            loading_progress.update(loading_task, completed=1)

        # Now run with the main progress bar
        with Progress(
                SpinnerColumn(finished_text="[green]✓"),
                TextColumn("{task.description}"),
                DateColumn(time_from),
                BarColumn(),
                CustomTimeElapsedColumn(),
                "/",
                CustomTimeRemainingColumn(),
        ) as progress:
            task = progress.add_task(
                description="Running script...",
                total=total_seconds,
            )

            # Create queue for progress updates
            progress_queue = queue.Queue()
            stop_event = threading.Event()

            def progress_worker():
                """Worker thread that updates progress bar at 60Hz"""
                last_update = 0
                while not stop_event.is_set():
                    try:
                        # Drain all pending updates
                        current_time = None
                        while True:
                            try:
                                current_time = progress_queue.get_nowait()
                            except queue.Empty:
                                break

                        # Update progress if we have new data
                        if current_time is not None:
                            if current_time == datetime.max:
                                current_time = time_to
                            elapsed_seconds = int((current_time - time_from).total_seconds())
                            # Only update if time changed (to avoid redundant updates)
                            if elapsed_seconds != last_update:
                                progress.update(task, completed=elapsed_seconds)
                                last_update = elapsed_seconds
                    except Exception:  # noqa
                        pass  # Ignore any errors in worker thread

                    # Wait ~33.33ms (30Hz refresh rate)
                    time.sleep(1 / 30)

            # Start worker thread
            worker = threading.Thread(target=progress_worker, daemon=True)
            worker.start()

            def cb_progress(current_time: datetime | None):
                """Callback that just puts timestamp in queue - near zero overhead"""
                try:
                    progress_queue.put_nowait(current_time)
                except queue.Full:
                    pass  # If queue is full, skip this update

            try:
                # Run the script
                runner.run(on_progress=cb_progress)

                # Ensure final progress update
                progress_queue.put(time_to)
                time.sleep(0.05)  # Give worker thread time to process final update

                progress.update(task, completed=total_seconds)
            finally:
                # Stop worker thread
                stop_event.set()
                worker.join(timeout=0.1)  # Wait max 100ms for thread to finish

                # Final update to ensure completion
                progress.refresh()

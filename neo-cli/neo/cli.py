"""Main Click-based CLI for neo."""
import sys
from typing import List, Optional, Tuple
import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from neo.backends import (
    get_all_backends,
    get_available_backends,
    get_backend,
    resolve_backend,
)
from neo.config import get_default_backend, load_config
from neo.utils import format_table, parse_package_spec

console = Console()

def extract_target_and_backend(
    target: Optional[str],
    backend_arg: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts the package name and backend alias from flexible inputs:
    - target="vim:ebuild", backend_arg=None -> ("vim", "ebuild")
    - target="vim", backend_arg=":ebuild" -> ("vim", "ebuild")
    - target=":ebuild", backend_arg=None -> (None, "ebuild")
    """
    pkg = target
    backend = None

    if backend_arg:
        b = backend_arg.strip()
        if b.startswith(":"):
            b = b[1:]
        backend = b

    if pkg:
        pkg_cleaned = pkg.strip()
        if pkg_cleaned.startswith(":"):
            # The target itself was a backend argument, e.g. 'neo update :ebuild'
            backend = pkg_cleaned[1:]
            pkg = None
        elif ":" in pkg_cleaned:
            parsed_pkg, parsed_backend = parse_package_spec(pkg_cleaned)
            pkg = parsed_pkg
            if parsed_backend:
                backend = parsed_backend

    return pkg, backend

@click.group(invoke_without_command=True)
@click.option("--version", "-v", is_flag=True, help="Show neo version and available backends.")
@click.pass_context
def cli(ctx: click.Context, version: bool):
    """neo - Unified Package Manager for Gentoo Linux."""
    if version:
        avail = get_available_backends()
        all_b = get_all_backends()
        default_b = get_default_backend()

        backend_status = []
        for alias, b in all_b.items():
            is_avail = alias in avail
            status_text = "[bold green]available[/]" if is_avail else "[bold red]not installed[/]"
            def_marker = " [cyan](default)[/]" if alias == default_b else ""
            backend_status.append(f"  • [bold]{alias}[/] ({b.name}){def_marker}: {status_text}")

        content = (
            "[bold white]neo[/] v0.1.0 - Gentoo Unified Package Manager\n\n"
            "[bold cyan]Registered Backends:[/]\n" + "\n".join(backend_status)
        )
        console.print(Panel(content, title="neo", border_style="cyan"))
        ctx.exit()

    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())

@cli.command("install")
@click.argument("package")
@click.argument("backend_opt", required=False)
def install_cmd(package: str, backend_opt: Optional[str] = None):
    """Install package: neo install <pkg> [:<backend>]"""
    pkg_name, backend_alias = extract_target_and_backend(package, backend_opt)

    if not pkg_name:
        console.print("[bold red]Error:[/] No package specified for installation.")
        sys.exit(1)

    backend = None
    if backend_alias:
        backend = get_backend(backend_alias)
        if not backend:
            console.print(f"[bold red]Error:[/] Unknown backend '{backend_alias}'.")
            sys.exit(1)
        if not backend.is_available():
            console.print(f"[bold red]Error:[/] Backend '{backend.name}' is not installed or available on this system.")
            sys.exit(1)
    else:
        # Auto-detect which available backend has this package
        avail = get_available_backends()
        candidates = []
        for alias, b in avail.items():
            results = b.search(pkg_name)
            if any(r.get("name", "").lower() == pkg_name.lower() or pkg_name.lower() in r.get("name", "").lower() for r in results):
                candidates.append((alias, b))

        if len(candidates) == 1:
            alias, backend = candidates[0]
            console.print(f"[bold blue][neo][/] Auto-detected backend [bold cyan]:{alias}[/] for package '{pkg_name}'.")
        elif len(candidates) > 1:
            console.print(f"[bold blue][neo][/] Package '{pkg_name}' found in multiple backends:")
            for i, (alias, b) in enumerate(candidates, 1):
                console.print(f"  [{i}] [bold cyan]:{alias}[/] ({b.name})")
            if sys.stdin.isatty():
                choice = Prompt.ask("Select backend number", choices=[str(i) for i in range(1, len(candidates) + 1)], default="1")
                backend = candidates[int(choice) - 1][1]
            else:
                backend = resolve_backend()
                console.print(f"[bold blue][neo][/] Defaulting to [bold cyan]:{backend.alias}[/].")
        else:
            backend = resolve_backend()

    console.print(Panel(
        f"Installing [bold green]{pkg_name}[/] using backend [bold cyan]:{backend.alias}[/] ({backend.name})...",
        title="neo install",
        border_style="green",
    ))

    success = backend.install(pkg_name)
    if success:
        console.print(f"[bold green]✓ Successfully installed {pkg_name} via :{backend.alias}![/]")
    else:
        console.print(f"[bold red]✗ Failed to install {pkg_name} via :{backend.alias}.[/]")
        sys.exit(1)

@cli.command("remove")
@click.argument("package")
@click.argument("backend_opt", required=False)
def remove_cmd(package: str, backend_opt: Optional[str] = None):
    """Remove package: neo remove <pkg> [:<backend>]"""
    pkg_name, backend_alias = extract_target_and_backend(package, backend_opt)

    if not pkg_name:
        console.print("[bold red]Error:[/] No package specified for removal.")
        sys.exit(1)

    if backend_alias:
        backend = get_backend(backend_alias)
        if not backend:
            console.print(f"[bold red]Error:[/] Unknown backend '{backend_alias}'.")
            sys.exit(1)
    else:
        backend = resolve_backend()

    console.print(Panel(
        f"Removing [bold yellow]{pkg_name}[/] using backend [bold cyan]:{backend.alias}[/] ({backend.name})...",
        title="neo remove",
        border_style="yellow",
    ))

    success = backend.remove(pkg_name)
    if success:
        console.print(f"[bold green]✓ Successfully removed {pkg_name} via :{backend.alias}![/]")
    else:
        console.print(f"[bold red]✗ Failed to remove {pkg_name} via :{backend.alias}.[/]")
        sys.exit(1)

@cli.command("search")
@click.argument("query")
@click.argument("backend_opt", required=False)
def search_cmd(query: str, backend_opt: Optional[str] = None):
    """Search packages: neo search <pkg> [:<backend>]"""
    q_str, backend_alias = extract_target_and_backend(query, backend_opt)
    if not q_str:
        q_str = query

    all_results: List[dict] = []

    if backend_alias:
        backend = get_backend(backend_alias)
        if not backend:
            console.print(f"[bold red]Error:[/] Unknown backend '{backend_alias}'.")
            sys.exit(1)
        with console.status(f"[bold green]Searching :{backend.alias} for '{q_str}'...[/]"):
            results = backend.search(q_str)
            all_results.extend(results)
    else:
        # Search all available backends
        avail = get_available_backends()
        with console.status(f"[bold green]Searching across {len(avail)} backends for '{q_str}'...[/]"):
            # Check if neo_core parallel search is available
            try:
                import neo_core
                backends_list = list(avail.keys())
                core_res = neo_core.parallel_search([q_str], backends_list)
                if isinstance(core_res, dict):
                    for b_key, items in core_res.items():
                        if isinstance(items, list):
                            all_results.extend(items)
            except Exception:
                for alias, b in avail.items():
                    try:
                        res = b.search(q_str)
                        all_results.extend(res)
                    except Exception as e:
                        console.print(f"[yellow]Warning: backend :{alias} search error: {e}[/]")

    if not all_results:
        console.print(f"[yellow]No packages found matching '{q_str}'.[/]")
        return

    table = format_table(
        all_results,
        columns=["name", "version", "backend", "installed", "description"],
        title=f"Search Results for '{q_str}' ({len(all_results)} found)",
    )
    console.print(table)

@cli.command("update")
@click.argument("backend_opt", required=False)
def update_cmd(backend_opt: Optional[str] = None):
    """Update packages: neo update [:<backend>]"""
    _, backend_alias = extract_target_and_backend(None, backend_opt)

    if backend_alias:
        targets = [get_backend(backend_alias)]
        if not targets[0]:
            console.print(f"[bold red]Error:[/] Unknown backend '{backend_alias}'.")
            sys.exit(1)
    else:
        avail = get_available_backends()
        targets = list(avail.values())

    for b in targets:
        if not b or not b.is_available():
            continue
        console.print(Panel(
            f"Updating packages for [bold cyan]:{b.alias}[/] ({b.name})...",
            title=f"neo update :{b.alias}",
            border_style="cyan",
        ))
        success = b.update()
        if success:
            console.print(f"[bold green]✓ Updated :{b.alias}[/]")
        else:
            console.print(f"[bold red]✗ Failed updating :{b.alias}[/]")

@cli.command("list")
@click.argument("backend_opt", required=False)
def list_cmd(backend_opt: Optional[str] = None):
    """List installed packages: neo list [:<backend>]"""
    _, backend_alias = extract_target_and_backend(None, backend_opt)

    all_installed: List[dict] = []

    if backend_alias:
        b = get_backend(backend_alias)
        if not b:
            console.print(f"[bold red]Error:[/] Unknown backend '{backend_alias}'.")
            sys.exit(1)
        with console.status(f"[bold green]Listing installed packages for :{b.alias}...[/]"):
            all_installed.extend(b.list_installed())
    else:
        avail = get_available_backends()
        with console.status("[bold green]Listing installed packages across all backends...[/]"):
            for alias, b in avail.items():
                try:
                    all_installed.extend(b.list_installed())
                except Exception as e:
                    console.print(f"[yellow]Warning: listing :{alias} failed: {e}[/]")

    table = format_table(
        all_installed,
        columns=["name", "version", "backend", "description"],
        title=f"Installed Packages ({len(all_installed)} total)",
    )
    console.print(table)

@cli.command("info")
@click.argument("package")
@click.argument("backend_opt", required=False)
def info_cmd(package: str, backend_opt: Optional[str] = None):
    """Package info: neo info <pkg> [:<backend>]"""
    pkg_name, backend_alias = extract_target_and_backend(package, backend_opt)

    if not pkg_name:
        console.print("[bold red]Error:[/] No package specified.")
        sys.exit(1)

    if backend_alias:
        backend = get_backend(backend_alias)
        if not backend:
            console.print(f"[bold red]Error:[/] Unknown backend '{backend_alias}'.")
            sys.exit(1)
    else:
        backend = resolve_backend()

    with console.status(f"[bold green]Retrieving info for {pkg_name} via :{backend.alias}...[/]"):
        info_data = backend.info(pkg_name)

    content = [
        f"[bold white]Package:[/] [green]{info_data.get('name', pkg_name)}[/]",
        f"[bold white]Backend:[/] [magenta]:{backend.alias}[/] ({backend.name})",
        f"[bold white]Version:[/] [yellow]{info_data.get('version', 'unknown')}[/]",
        f"[bold white]Status:[/] {'[bold green]Installed[/]' if info_data.get('installed') else '[cyan]Available[/]'}",
    ]
    if info_data.get("description"):
        content.append(f"[bold white]Description:[/] {info_data['description']}")
    if info_data.get("homepage"):
        content.append(f"[bold white]Homepage:[/] [blue underline]{info_data['homepage']}[/]")

    if info_data.get("raw"):
        content.append("\n[bold white]Output:[/] \n" + info_data["raw"])

    console.print(Panel("\n".join(content), title=f"Package Info: {pkg_name}", border_style="cyan"))

@cli.command("sync")
@click.argument("backend_opt", required=False)
def sync_cmd(backend_opt: Optional[str] = None):
    """Sync package databases: neo sync [:<backend>]"""
    _, backend_alias = extract_target_and_backend(None, backend_opt)

    if backend_alias:
        targets = [get_backend(backend_alias)]
        if not targets[0]:
            console.print(f"[bold red]Error:[/] Unknown backend '{backend_alias}'.")
            sys.exit(1)
    else:
        avail = get_available_backends()
        targets = list(avail.values())

    for b in targets:
        if not b or not b.is_available():
            continue
        console.print(Panel(
            f"Syncing package database for [bold cyan]:{b.alias}[/] ({b.name})...",
            title=f"neo sync :{b.alias}",
            border_style="magenta",
        ))
        success = b.sync()
        if success:
            console.print(f"[bold green]✓ Synced :{b.alias}[/]")
        else:
            console.print(f"[bold red]✗ Failed syncing :{b.alias}[/]")

@cli.command("clean")
@click.argument("backend_opt", required=False)
def clean_cmd(backend_opt: Optional[str] = None):
    """Clean cache: neo clean [:<backend>]"""
    _, backend_alias = extract_target_and_backend(None, backend_opt)

    # Clean Rust core cache
    try:
        import neo_core
        neo_core.clear_cache()
        console.print("[bold green]✓ Cleared neo core local cache (~/.cache/neo)[/]")
    except Exception as e:
        console.print(f"[yellow]Warning clearing core cache: {e}[/]")

    if backend_alias:
        b = get_backend(backend_alias)
        if b and b.is_available():
            console.print(f"Cleaning cache for [bold cyan]:{b.alias}[/]...")
            b.clean()
    else:
        avail = get_available_backends()
        for alias, b in avail.items():
            console.print(f"Cleaning cache for [bold cyan]:{alias}[/]...")
            b.clean()

    console.print("[bold green]✓ Cache clean complete![/]")

def main():
    cli()

if __name__ == "__main__":
    main()

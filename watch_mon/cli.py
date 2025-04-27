import typer

from watch_mon.api.mcp_server import mcp

app = typer.Typer(help="Monad Chain Protocol - A tool for monitoring and analyzing dApps on Monad testnet")


@app.command()
def serve(
    stdio: bool = typer.Option(True, help="Use stdio mode"),
):
    """Start the MCP server"""
    if stdio:
        mcp.run()
    else:
        raise Exception("not support")


@app.command()
def version():
    """Show the version of watch-mon"""
    import pkg_resources

    version = pkg_resources.get_distribution("watch-mon").version
    typer.echo(f"watch-mon version {version}")


def main():
    app()


if __name__ == "__main__":
    main()

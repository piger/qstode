try:
    import bjoern

    has_bjoern = True
except ImportError:
    has_bjoern = False

from qstode.main import create_app


# WSGI entry point
app = create_app()

@app.cli.command()
def wsgi():
    if has_bjoern:
        bjoern.run(app, "127.0.0.1", 5000)
    else:
        click.echo("bjoern is not available")

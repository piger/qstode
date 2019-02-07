try:
    import bjoern

    has_bjoern = True
except ImportError:
    has_bjoern = False

from ..app import app


if has_bjoern:
    @app.cli.command()
    def wsgi():
        from ..main import create_app
        bjoern.run(create_app(), '127.0.0.1', 5000)

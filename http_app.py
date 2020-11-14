from routing_packager_app import create_app, cli, db
from routing_packager_app.api_v1 import User, Job

app = create_app()
cli.register(app)


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Job': Job}

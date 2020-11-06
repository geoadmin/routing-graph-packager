from kadas_routing_http import create_app, cli, db
from kadas_routing_http.api_v1 import User, Job

app = create_app('production')
cli.register(app)


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Job': Job}

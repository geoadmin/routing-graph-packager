from routing_packager_app.logger import LOGGING_CONFIG

bind = "0.0.0.0:5000"
workers = 1
worker_class = "uvicorn.workers.UvicornWorker"
logconfig_dict = LOGGING_CONFIG 

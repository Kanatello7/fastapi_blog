import multiprocessing

# server
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
timeout = 30

# logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

from rq import Worker, Queue, Connection

with Connection():
    worker = Worker([Queue("packaging")])
    worker.work(burst=True)

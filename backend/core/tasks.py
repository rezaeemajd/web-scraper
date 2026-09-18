from celery import shared_task
@shared_task
def heartbeat(): return "cdi-worker-ok"

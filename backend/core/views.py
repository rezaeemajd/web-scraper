from django.db import connection
from django.http import JsonResponse

def health(request): return JsonResponse({"status":"ok","service":"cdi-backend"})
def ready(request):
    try:
        with connection.cursor() as c: c.execute("SELECT 1")
        return JsonResponse({"status":"ready","database":"ok"})
    except Exception as exc:
        return JsonResponse({"status":"not_ready","database":"error","detail":str(exc)},status=503)

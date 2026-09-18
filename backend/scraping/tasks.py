from celery import shared_task
@shared_task
def run_scraper(scraper_id):
    from .models import ScraperRun
    run=ScraperRun.objects.create(scraper_id=scraper_id)
    return {"run_id":run.id,"status":run.status}

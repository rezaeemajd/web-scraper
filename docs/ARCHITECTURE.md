# CDI Architecture

CDI is a modular Django/DRF backend with PostgreSQL persistence, Redis/Celery background execution, and a Next.js RTL frontend. Scraping follows Fetch -> Raw Capture -> Parse -> Extract -> Normalize -> Validate -> Deduplicate -> Quality -> Save.

P0 deliberately keeps browser automation and heavy analytics disabled for the 2GB production host.

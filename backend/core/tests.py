from django.test import TestCase
class HealthTests(TestCase):
    def test_health(self):
        r=self.client.get("/health/"); self.assertEqual(r.status_code,200); self.assertEqual(r.json()["status"],"ok")

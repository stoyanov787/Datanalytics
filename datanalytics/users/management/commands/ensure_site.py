from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

class Command(BaseCommand):
    help = 'Ensures the default site exists'

    def handle(self, *args, **kwargs):
        Site.objects.update_or_create(
            id=1,
            defaults={
                # use env variable
                'domain': 'http://127.0.0.1:8000/',
                'name': 'Datanalytics'
            }
        )
        self.stdout.write(self.style.SUCCESS('Successfully created/updated default site'))
from api.models import ModelBackend
from django.core.management.base import BaseCommand
from django.db import DatabaseError
from django.conf import settings


class Command(BaseCommand):
    help = 'Non-interactively create available model backends'

    def handle(self, *args, **options):
        ModelBackend.initialize_data()

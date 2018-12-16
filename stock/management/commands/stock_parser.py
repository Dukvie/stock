from django.core.management.base import BaseCommand, CommandError

from stock.utils import Parser


class Command(BaseCommand):
    help = 'Парсер данных цен акций'

    def add_arguments(self, parser):
        parser.add_argument('threads', type=int, default=1)

    def handle(self, *args, **options):
        threads = options['threads']
        if threads < 1:
            raise CommandError('Количество потоков должно быть целым числом больше нуля')
        Parser().parse(threads)

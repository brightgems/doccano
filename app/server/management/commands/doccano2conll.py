try:
    from doccano2conll import doccano_to_conll
except ImportError:
    import os.path
    from sys import path as sys_path
    # Guessing that we might be in the brat tools/ directory ...
    sys_path.append('../active_learn/src')
    from doccano2conll import doccano_to_conll
from tokenizer import Tokenizer
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = ''

    @classmethod
    def add_arguments(self, parser):
        parser.add_argument('--projectname', default=None,
                            help='The name of the project.')

    def handle(self, *args, **options):
        projectname = options.get('projectname')
        output_filepath = options.get('output_filepath')
        if not projectname:
            raise CommandError('--projectname are required')

        try:
            tokenizer = Tokenizer('jieba')
            doccano_to_conll(projectname, tokenizer, split_sentences=True)
            self.stdout.write(self.style.SUCCESS('Conll created successfully "%s"' % projectname))
        except Exception as ex:
            import traceback
            traceback.print_exc()
            self.stderr.write(self.style.ERROR('Error occurred while generate conll "%s"' % ex))

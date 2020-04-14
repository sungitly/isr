# -*- coding: utf-8 -*-
import os

from flask import current_app
from flask.ext.script import Manager

LookupCommand = Manager(usage='Perform Lookup Data Operations')


def _get_config():
    from alembic.config import Config
    migrations_dir = os.path.join(current_app.config['PROJECT_ROOT'], 'isr', 'migrations')
    config = Config(os.path.join(migrations_dir, 'alembic.ini'))
    config.set_main_option('script_location', migrations_dir)
    config.set_main_option('sqlalchemy.url', current_app.config.get('SQLALCHEMY_DATABASE_URI'))
    return config


def _run_with_alembic_context(func, *args, **kwargs):
    from alembic.runtime.environment import EnvironmentContext
    from alembic import context
    from alembic.script import ScriptDirectory
    from sqlalchemy import engine_from_config
    from alembic.operations import Operations
    from sqlalchemy import pool

    config = _get_config()
    script_directory = ScriptDirectory.from_config(config)
    with EnvironmentContext(config, script_directory):
        connectable = engine_from_config(
                config.get_section(config.config_ini_section),
                prefix='sqlalchemy.',
                poolclass=pool.NullPool)

        with connectable.connect() as connection:
            context.configure(connection=connection)
            with context.begin_transaction():
                with Operations.context(context.get_context()):
                    func(*args, **kwargs)


@LookupCommand.option('-s', '--store', dest='store_id', required=True)
def setup(store_id):
    """
    Setup lookups for the specified store using seed lookup data
    """

    def _setup(store_id):
        from application.nutils.csvloader import load_all_lookupvalue_from_csv
        from application.nutils.csvloader import load_lookup_from_csv
        load_lookup_from_csv('data/lookup.csv', store_id_override=store_id)
        load_all_lookupvalue_from_csv('data/lookupvalue', store_id)

    _run_with_alembic_context(_setup, store_id)


@LookupCommand.option('--id', dest='lookup_id', required=True)
@LookupCommand.option('-l', '--location', dest='csv_location', required=False)
def reload(lookup_id, csv_location):
    """
    reload lookupvalues for the specified lookup using the data from csv file.
    """

    def _reload(lookup_id, csv_location):
        from application.nutils.csvloader import find_lookup_basic_info_by_id
        from application.nutils.csvloader import load_lookupvalue_from_csv
        from application.nutils.csvloader import update_lookup_version

        lookup = find_lookup_basic_info_by_id(lookup_id)
        if not lookup:
            raise Exception('Lookup with id %s does not exist' % lookup_id)
        if not csv_location:
            csv_location = os.path.join(current_app.config['DATA_FOLDER'], 'lookupvalue', '%s.csv' % lookup.name)

        load_lookupvalue_from_csv(csv_location, lookup_id, version=lookup.version + 1)
        update_lookup_version(lookup_id, lookup.version + 1)

    _run_with_alembic_context(_reload, lookup_id, csv_location)


BabelCommand = Manager(usage='Perform Translation Operations')


@BabelCommand.command
def generate():
    os.system('pybabel extract application -o application/translations/base.pot')


@BabelCommand.option('-l', '--locale', dest='locale', required=True, default='zh')
def init(locale):
    os.system('pybabel init -d application/translations -i application/translations/base.pot -l %s' % locale)


@BabelCommand.option('-l', '--locale', dest='locale', required=True, default='zh')
def update(locale):
    os.system('pybabel update -d application/translations -i application/translations/base.pot -l %s' % locale)


@BabelCommand.command
def compile():
    os.system('pybabel compile -d application/translations -f')

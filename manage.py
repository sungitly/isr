# -*- coding: utf-8 -*-
import binascii

import os
from application import create_app
from application.models.base import db
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager, Server
from tools.command import BabelCommand
from tools.command import LookupCommand

PORT = 5000

app = create_app()
manager = Manager(app)
manager.add_command("runserver", Server(host="0.0.0.0", port=PORT))

# db migrate commands
# Run python manage.py db upgrade to upgrade database
# Run python manage.py db --help to get help
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)
manager.add_command('lookup', LookupCommand)
manager.add_command('babel', BabelCommand)


# Flask-Script provide shell and runserver command by default.


# utilities
@manager.command
def dropdb():
    """
    Delete all tables
    """
    db.drop_all()
    db.engine.execute('DROP TABLE IF EXISTS alembic_version')


@manager.command
def generate_app_keys():
    """
    generate app keys and corresponding secret key for API access (HMAC auth)
    """
    print('generated app key without prefix is:')
    print(binascii.hexlify(os.urandom(8)))

    print('generated secret key without prefix is:')
    print(binascii.hexlify(os.urandom(16)))


@manager.command
def migrate_user_data_to_ucenter():
    """
    .. deprecated:: the function was used to migrate user data to new structure after ucenter is introduced.
    """
    from tools.db_migrations import user_data_to_ucenter
    with app.app_context():
        user_data_to_ucenter()


if __name__ == "__main__":
    manager.run()

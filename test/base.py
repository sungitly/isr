# coding: utf-8
import unittest

from application import create_app
from application.models.base import db



class BaseTestCase(unittest.TestCase):
    rebuild_db = True
    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.app = create_app('test')
        self.client = self.app.test_client()

        self.setup_run_in_appcontent()

    def tearDown(self):
        return

    def setup_run_in_appcontent(self):
        '''
        初始化代码需要在app.context环境下运行的
        '''
        if self.rebuild_db:
            self.run_in_appcontext(db.drop_all)
            self.run_in_appcontext(db.create_all)

    def run_in_appcontext(self, func):
        with self.app.app_context():
            func()

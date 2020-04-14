# -*- coding: utf-8 -*-
import datetime

from .base import db
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, func


class JobsRecord(db.Model):
    __tablename__ = 'jobsrecord'

    id = Column(BigInteger, primary_key=True)
    start_time = Column(DateTime, default=datetime.datetime.now)
    end_time = Column(DateTime)
    jobname = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default='success')
    message = Column(String(100), default='')
    json_result = Column(String(150))
    duration = Column(Integer, default=0)

    def complete(self):
        self.end_time = datetime.datetime.now()
        self.duration = (self.end_time - self.start_time).seconds

    def save(self):
        if self.id is None:
            db.session.add(self)
        elif self not in db.session:
            db.session.merge(self)

    def save_and_flush(self):
        self.save()
        db.session.flush()

    @classmethod
    def get_job_result_by_date(cls, jobname, start_time):
        return cls.query.filter(
            db.and_(cls.jobname == jobname, func.date(cls.start_time) == start_time, cls.status == 'success')).all()

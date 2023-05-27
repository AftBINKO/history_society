from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, orm, DateTime
from sqlalchemy_serializer import SerializerMixin

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    serialize_rules = ()

    id = Column(Integer, primary_key=True, autoincrement=True)

    fullname = Column(String, nullable=False)

    login = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    status = Column(String, ForeignKey("statuses.id"), nullable=False, default=1)
    st = orm.relationship('Status')

    def __repr__(self):
        return f"<User {self.fullname}>"

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def get_columns(self):
        return [column.key for column in self.__table__.columns]


class Status(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'statuses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)

    user = orm.relationship("User", back_populates="st")

    def __repr__(self):
        return f"<Status {self.title}>"

    def get_columns(self):
        return [column.key for column in self.__table__.columns]

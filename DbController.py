# todo: check errors
import sqlalchemy.sql.ddl
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, insert, delete, update
from sqlalchemy.orm import Session, DeclarativeBase, relationship

from Strings import DB


class Base(DeclarativeBase):
    ...

# class Serialize(Base):
#     __tablename__ = 'serialize'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     chat_id = Column(Integer)
#     args= Column(String)
class Mail(Base):
    __tablename__ = 'mail'

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(String)



    def __repr__(self):
        return f'hi'


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer)
    isWised = Column(Boolean, default=False)
    isSanta = Column(Boolean, default=False)
    name = Column(String)
    secret = Column(Integer)
    mail = relationship("Mail")


class Database():
    def __init__(self):
        self.__engine = create_engine(DB, echo=False)
        self.session = Session(self.__engine)
        Base.metadata.create_all(self.__engine)

    def get_count_wished(self):
        return self.session.query(User).filter(User.isWised == True).count()

    def insert(self, table, returning=None, **values):
        if returning:
            returns = self.session.execute(insert(table).values(**values).returning(returning)).fetchone()
            self.session.commit()

            return returns
        else:
            self.session.execute(insert(table).values(**values))
            self.session.commit()

    def update(self, table, filter, returning, **values):
        returns= self.session.execute(update(table).where(*filter).values(**values).returning(returning))
        self.session.commit()
        return returns


    def select(self, table, filter=(True,), count=False, one=False):
        if count:
            return self.session.query(table).filter(*filter).count()
        else:
            return self.session.query(table).filter(*filter).one() if one else self.session.query(table).filter(
                *filter).all()

    def delete(self, table, filter: list, returning=None):
        if returning:
            returns = self.session.execute(delete(table).returning(returning)).fetchone()
            self.session.commit()
            return returns
        else:
            self.session.query(table).filter(*filter).delete()
            self.session.commit()


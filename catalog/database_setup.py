import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

 
class Brand(Base):
    __tablename__ = 'brand'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    pic = Column(String(80),nullable=False)
    description = Column(String(250),nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)



    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'pic': self.pic,
            'id': self.id,
            'description': self.description,
            'user_id':self.user_id,
        }


class Mobile(Base):

  __tablename__ = 'mobiles'


  name = Column(String(80), nullable=False)
  image = Column(String(80),nullable=False)
  id = Column(Integer, primary_key=True)
  description = Column(String(250))
  price = Column(String(80))
  rating = Column(String(80),nullable=False)
  offer = Column(String(80))
  brand_id= Column(Integer,ForeignKey('brand.id'))
  user_id = Column(Integer, ForeignKey('user.id'))
  user = relationship(User)
  brand=relationship(Brand)

  @property
  def serialize(self):
    """Return object data in easily serializeable format"""
    return {
        'name': self.name,
        'image': self.image,
        'description': self.description,
        'id': self.id,
        'price': self.price,
        'rating': self.rating,
        'offer': self.offer,
        'user_id': self.user_id,
    }

engine = create_engine('sqlite:///mobiledb.db')
 

Base.metadata.create_all(engine)
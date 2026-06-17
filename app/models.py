from sqlalchemy import Column, Integer, BigInteger, String, LargeBinary

from db import Base


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    store = Column(String, nullable=False)
    encrypted_data = Column(LargeBinary, nullable=False)

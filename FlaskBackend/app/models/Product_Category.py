from .db import get_db
from datetime import datetime

class Product_Category():
    def __init__(self, productId = None, categoryId = None, productOrigin = None, categoryOrigin = None, createAt = None):
        self.productId = productId
        self.categoryId = categoryId
        self.productOrigin = productOrigin
        self.categoryOrigin = categoryOrigin
        self.createAt = createAt
    
    @classmethod
    def delete_by_origin(cls, origin):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'DELETE FROM Product_Category WHERE productOrigin = %s',
                (origin,)
            )
            db.commit()

    def add(self):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'INSERT INTO Product_Category (productId, categoryId, productOrigin, categoryOrigin) VALUES (%s,%s,%s,%s)',
                (self.productId, self.categoryId, self.productOrigin, self.categoryOrigin)
            )
            db.commit()
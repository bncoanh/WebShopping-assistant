from .db import get_db
from datetime import datetime

class ProductHistory():
    def __init__(self, accountId = None, productId = None, origin = None, createAt = None):
        self.accountId = accountId
        self.productId = productId
        self.origin = origin
        self.createAt = createAt
    
    @classmethod
    def get_product_histories_by_origin(cls, origin):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'SELECT * FROM ProductHistory WHERE origin = %s',
                (origin,)
            )
            histories = cursor.fetchall()
        result = []
        for h in histories:
            result.append(
                ProductHistory(h['accountId'], h['productId'], h['origin'], h['createAt'])
            )
        return result

    @classmethod
    def delete_by_origin(cls, origin):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'DELETE FROM ProductHistory WHERE origin = %s',
                (origin,)
            )
            db.commit()
    
    def add(self):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'INSERT INTO ProductHistory (accountId, productId, origin, createAt) VALUES (%s,%s,%s,%s)',
                (self.accountId, self.productId, self.origin, self.createAt),
            )
            db.commit()
    
    @classmethod
    def get_product_histories_by_accountId(cls, accountId):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'SELECT * FROM ProductHistory WHERE accountId = %s',
                (accountId,)
            )
            histories = cursor.fetchall()
        result = []
        for h in histories:
            result.append(
                ProductHistory(h['accountId'], h['productId'], h['origin'], h['createAt'])
            )
        return result
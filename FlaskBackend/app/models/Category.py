from .db import get_db
from datetime import datetime

class Category():
    def __init__(self, categoryId = None, origin = None, name = None, imgURL = None, isLeaf = None, parentId = None, parentOrigin = None, createAt = None):
        self.categoryId = categoryId
        self.origin = origin
        self.name = name
        self.imgURL = imgURL
        self.isLeaf = isLeaf
        self.parentId = parentId
        self.parentOrigin = parentOrigin
        self.createAt = createAt
    
    @classmethod
    def delete_by_origin(cls, origin):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
            cursor.execute(
                'DELETE FROM Category WHERE origin = %s',
                (origin,)
            )
            cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
            db.commit()
    
    def add(self):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'INSERT INTO Category (categoryId, origin, name, imgUrl, isLeaf) VALUES (%s,%s,%s,%s,%s)',
                (self.categoryId, self.origin, self.name, self.imgURL, self.isLeaf)
            )
            db.commit()
    
    @classmethod
    def update_parentId_parentOrigin(cls, categoryId, origin, parentId):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'UPDATE Category SET parentId = %s, parentOrigin = %s WHERE categoryId = %s AND origin = %s',
                (parentId, origin if parentId else None, categoryId, origin)
            )
            db.commit()
    
    @classmethod
    def get_categories_by_origin(cls, origin):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'SELECT * FROM Category WHERE origin = %s',
                (origin, )
            )
            categories = cursor.fetchall()
        res = []
        for c in categories:
            res.append(
                Category(c['categoryId'], c['origin'], c['name'], c['imgURL'], c['isLeaf'], c['parentId'], c['parentOrigin'], c['createAt'])
            )
        return res
    
    @classmethod
    def get_categories_by_productId_origin(cls, productId, origin):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                '''
                SELECT c.categoryId, c.origin, c.name, c.imgURL, c.isLeaf, c.parentId, c.parentOrigin, c.createAt
                FROM Product_Category AS pc
                JOIN Category AS c ON c.categoryId = pc.categoryId AND c.origin = pc.categoryOrigin
                WHERE pc.productId = %s AND c.origin = %s
                ''',
                (productId, origin)
            )
            categories = cursor.fetchall()
        res = []
        for c in categories:
            res.append(
                Category(c['categoryId'], c['origin'], c['name'], c['imgURL'], c['isLeaf'], c['parentId'], c['parentOrigin'], c['createAt'])
            )
        return res
    
    @classmethod
    def get_categories_by_parentId_origin(cls, parentId, origin):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'SELECT * FROM Category WHERE parentId = %s AND origin = %s',
                (parentId, origin)
            )
            categories = cursor.fetchall()
        res = []
        for c in categories:
            res.append(
                Category(c['categoryId'], c['origin'], c['name'], c['imgURL'], c['isLeaf'], c['parentId'], c['parentOrigin'], c['createAt'])
            )
        return res
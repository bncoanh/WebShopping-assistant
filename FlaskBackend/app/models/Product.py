from .db import get_db
from datetime import datetime

class Product():
    def __init__(self, productId = None, origin = None, imgURL = None, name = None, link = None, quantitySold = None, price = None, reviewCount = None, rating = None, sellerName = None, brandName = None, createAt = None):
        self.productId = productId
        self.origin = origin
        self.imgURL = imgURL
        self.name = name
        self.link = link
        self.quantitySold = quantitySold
        self.price = price
        self.reviewCount = reviewCount
        self.rating = rating
        self.sellerName = sellerName
        self.brandName = brandName
        self.createAt = createAt

    @classmethod
    def delete_by_origin(cls, origin):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'DELETE FROM Product WHERE origin = %s',
                (origin,)
            )
            db.commit()
    
    def add(self):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'INSERT INTO Product (productId, origin, imgURL, name, link, quantitySold, price, reviewCount, rating, sellerName, brandName) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (self.productId, self.origin, self.imgURL, self.name, self.link, self.quantitySold, self.price, self.reviewCount, self.rating, self.sellerName, self.brandName)
            )
            db.commit()
    
    @classmethod
    def get_products_by_origin(cls, origin):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'SELECT * FROM Product WHERE origin = %s',
                (origin,)
            )
            products = cursor.fetchall()
        res = []
        for p in products:
            res.append(
                Product(p['productId'], p['origin'], p['imgURL'], p['name'], p['link'], p['quantitySold'], p['price'], p['reviewCount'], p['rating'], p['sellerName'], p['brandName'], p['createAt'])
            )
        return res
    
    @classmethod
    def get_products(cls):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT * FROM Product')
            products = cursor.fetchall()
        res = []
        for p in products:
            res.append(
                Product(p['productId'], p['origin'], p['imgURL'], p['name'], p['link'], p['quantitySold'], p['price'], p['reviewCount'], p['rating'], p['sellerName'], p['brandName'], p['createAt'])
            )
        return res
    
    @classmethod
    def get_products_by_category(cls, origin, categoryId):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                 '''SELECT Product.productId, Product.origin, Product.imgURL, Product.name, Product.link, Product.quantitySold, Product.price, Product.reviewCount, Product.rating, Product.sellerName, Product.brandName, Product.createAt
                FROM Category
                JOIN Product_Category ON Category.categoryId = Product_Category.categoryId AND Category.origin = Product_Category.categoryOrigin
                JOIN Product ON Product.productId = Product_Category.productId AND Product.origin = Product_Category.productOrigin
                WHERE Category.categoryId = %s AND Category.origin = %s
                ''',
                (categoryId, origin)
            )
            products = cursor.fetchall()
        res = []
        for p in products:
            res.append(
                Product(p['productId'], p['origin'], p['imgURL'], p['name'], p['link'], p['quantitySold'], p['price'], p['reviewCount'], p['rating'], p['sellerName'], p['brandName'], p['createAt'])
            )
        return res
    
    @classmethod
    def get_products_by_category_order(cls, origin, categoryId, order_by, type):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                 '''SELECT Product.productId, Product.origin, Product.imgURL, Product.name, Product.link, Product.quantitySold, Product.price, Product.reviewCount, Product.rating, Product.sellerName, Product.brandName, Product.createAt
                FROM Category
                JOIN Product_Category ON Category.categoryId = Product_Category.categoryId AND Category.origin = Product_Category.categoryOrigin
                JOIN Product ON Product.productId = Product_Category.productId AND Product.origin = Product_Category.productOrigin
                WHERE Category.categoryId = %s AND Category.origin = %s
                ORDER BY {0} {1}
                '''.format('Product.' + order_by, type),
                (categoryId, origin)
            )
            products = cursor.fetchall()
        res = []
        for p in products:
            res.append(
                Product(p['productId'], p['origin'], p['imgURL'], p['name'], p['link'], p['quantitySold'], p['price'], p['reviewCount'], p['rating'], p['sellerName'], p['brandName'], p['createAt'])
            )
        return res
    
    @classmethod
    def get_product_by_productId_origin(cls, productId, origin):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'SELECT * FROM Product WHERE productId = %s AND origin = %s',
                (productId, origin)
            )
            product = cursor.fetchone()
        if product is None:
            return None
        else:
            return Product(product['productId'], product['origin'], product['imgURL'], product['name'], product['link'], product['quantitySold'], product['price'], product['reviewCount'], product['rating'], product['sellerName'], product['brandName'], product['createAt'])
    
    @classmethod
    def get_product_by_productId(cls, productId):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'SELECT * FROM Product WHERE productId = %s',
                (productId,)
            )
            product = cursor.fetchone()
        if product is None:
            return None
        else:
            return Product(product['productId'], product['origin'], product['imgURL'], product['name'], product['link'], product['quantitySold'], product['price'], product['reviewCount'], product['rating'], product['sellerName'], product['brandName'], product['createAt'])
from .db import get_db
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

class Account():
    def __init__(self, accountId = None, username = None, password = None, isAdmin = None, createAt = None, updateAt = None):
        self.accountId = accountId
        self.username = username
        self.password = password
        self.isAdmin = isAdmin
        self.createAt = createAt
        self.updateAt = updateAt
    
    def add(self):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                'INSERT INTO Account (username, password, isAdmin) VALUES (%s, %s, %s)',
                (self.username, generate_password_hash(self.password), self.isAdmin)
            )
        db.commit()
    
    @classmethod
    def get_account_by_username_password(cls, username, password):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'SELECT * FROM Account WHERE username = %s', (username, )
            )
            account = cursor.fetchone()
        if account is None or not check_password_hash(account['password'], password):
            return None
        else:
            return Account(account['accountId'], account['username'], account['password'], account['isAdmin'], account['createAt'], account['updateAt'])
    
    @classmethod
    def get_account_by_accountId(cls, accountId):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'SELECT * FROM Account WHERE accountId = %s', (accountId,)
            )
            account = cursor.fetchone()
        if account is None:
            return None
        return Account(account['accountId'], account['username'], account['password'], account['isAdmin'], account['createAt'], account['updateAt'])
    
    @classmethod
    def update_password_by_accountId(cls, newPassword, accountId):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                    'UPDATE Account SET password = %s WHERE accountId = %s', (generate_password_hash(newPassword), accountId)
                )
            db.commit()
    
    @classmethod
    def get_users(cls):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'SELECT * FROM Account WHERE isAdmin = 0'
            )
            users = cursor.fetchall()
        result = []
        for u in users:
            result.append(Account(u['accountId'], u['username'], u['password'], u['isAdmin'], u['createAt'], u['updateAt']))
        return result
    
    @classmethod
    def get_user_by_accountId(cls, accountId):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'SELECT * FROM Account WHERE accountId = %s AND isAdmin = 0',
                (accountId,)
            )
            user = cursor.fetchone()
        if user is None:
            return None
        return Account(user['accountId'], user['username'], user['password'], user['isAdmin'], user['createAt'], user['updateAt'])
    
    @classmethod
    def delete_user_by_accountId(cls, accountId):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                'DELETE FROM Account WHERE accountId = %s AND isAdmin = 0',
                (accountId,)
            )
            db.commit()
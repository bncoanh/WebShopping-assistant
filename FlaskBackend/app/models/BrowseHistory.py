from .db import get_db
from datetime import datetime

class BrowseHistory():
    def __init__(self, browseId= None, content = None, accountId = None, createAt = None):
        self.browseId = browseId
        self.content = content
        self.accountId = accountId
        self.createAt = createAt

    def add(self):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'INSERT INTO BrowseHistory (browseId, content, accountId, createAt) VALUES (%s,%s,%s,%s)',
                (self.browseId, self.content, self.accountId, self.createAt)
            )
            db.commit()

    @classmethod
    def get_10_histories_by_accountId(cls, accountId):
        db = get_db()
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(
                'SELECT * FROM BrowseHistory WHERE accountId = %s ORDER BY browseId DESC LIMIT 10',
                (accountId,)
            )
            histories = cursor.fetchall()
        result = []
        for h in histories:
            result.append(
                BrowseHistory(h['browseId'], h['content'], h['accountId'], h['createAt'])
            )
        return result
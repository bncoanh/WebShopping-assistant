from mysql.connector import connect, Error
from werkzeug.security import check_password_hash, generate_password_hash
import click
from flask import current_app, g

def get_db():
    """
    Connects to the database and returns the connection object.

    If the database does not exist, it creates it. If the connection object
    does not exist, it creates it. Otherwise, it returns the existing
    connection object.

    The connection object is stored in the g object, which is a special
    object in Flask that is unique for each request. This allows multiple
    requests to share the same connection object.

    :return: The connection object.
    :rtype: mysql.connector.connection.MySQLConnection
    """
    if 'db' not in g:
        try:
            g.db = connect(
                host="localhost",
                user='root',
                password='12345',
            )
            create_db_query = "CREATE DATABASE IF NOT EXISTS ShoppingAssistant"
            with g.db.cursor() as cursor:
                cursor.execute(create_db_query)
            g.db.close()
            g.db = connect(
                host="localhost",
                user='root',
                password='12345',
                database='ShoppingAssistant'
            )
            print('Connected to database')
        except Error as e:
            print(e)

    return g.db

def close_db(e=None):
    """
    Close the database connection.

    This function is registered as a teardown function for the Flask application
    context. It is called after each request is processed, and it closes the
    database connection. This is necessary to prevent the database connection
    from being left open after the request is processed.

    :param e: An error object, which is ignored.
    :type e: Exception
    """
    db = g.pop('db', None)

    if db is not None:
        db.close()
        print('Database connection closed')

def init_db():
    """ 
    Create the tables in the database if they do not exist.

    This function reads the SQL script from the file
    `ShoppingAssistant.sql` and executes it. If the `Account` table is empty,
    it will also add the first admin account with the username "admin" and
    password "admin".

    :return: None
    """
    db = get_db()

    with current_app.open_resource('ShoppingAssistant.sql') as f:
        sql_script = f.read().decode('utf8')
    
    with db.cursor() as cursor:
        try:
            for q in sql_script.split(';'):
                cursor.execute(q)
            db.commit()
            print('Created tables if they do not exist')
        except Error as e:
            print(e)
            db.rollback()
    
    try:
        add_first_admin_query = 'INSERT INTO Account (username, password, isAdmin) VALUES ("admin", %s, 1)'
        with db.cursor() as cursor:
            cursor.execute(add_first_admin_query, (generate_password_hash("admin"),))
        db.commit()
        
        add_first_user_query = 'INSERT INTO Account (username, password, isAdmin) VALUES ("user1", %s, 0)'
        with db.cursor() as cursor:
            cursor.execute(add_first_user_query, (generate_password_hash("user1"),))
        db.commit()
    except Error as e:
        print(e)

@click.command('init-db')
def init_db_command():
    """Create the tables in the database.

    This command creates the tables in the database if they do not exist.
    If the `Account` table is empty, it will also add the first admin account
    with the username "admin" and password "admin".

    :return: None
    """
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    """
    Initialize the database for the Flask application.

    This function registers the teardown function `close_db` with the Flask
    application context, and adds the `init-db` command to the Flask CLI.

    :param app: The Flask application object.
    :type app: Flask
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
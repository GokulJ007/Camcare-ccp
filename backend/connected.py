import pymysql
import pymysql.cursors

def db_connect():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='Gokulj7959$',
            database='camcare',
            port=3030,
            cursorclass=pymysql.cursors.DictCursor,
        )
        return connection
    except pymysql.MySQLError as e:
        raise Exception("error in connection to db") from e 

import pymysql
from util.CommonUtils import *
import util.Config as config

mysql_host = config.mysql_info.host
mysql_user = config.mysql_info.username
mysql_password = config.mysql_info.password
mysql_db = config.mysql_info.db_name
mysql_port = config.mysql_info.port


def get_insert_head(table_name, fields):
    if type(fields) == str:
        return "INSERT INTO {0}({1}) ".format(table_name, fields)
    if type(fields) == list:
        return "INSERT INTO {0}({1}) ".format(table_name, ", ".join(fields))
    printError("未识别的fields:")
    printError(fields)
    return ""


def get_insert_body(values):
    body = []
    for value in values:
        body.append(wrap_value(value))
    return "VALUES({})".format(", ".join(body))


def get_insert_bodies(values_list):
    bodies = []
    for values in values_list:
        body = []
        for value in values:
            body.append(wrap_value(value))
        bodies.append("({})".format(", ".join(body)))
    return "VALUES{}".format(", ".join(bodies))


def wrap_value(value):
    if type(value) != str:
        return '"{}"'.format(str(value).replace("\"", "\\\""))
    if value.startswith('"') and value.endswith('"'):
        return "\"" + value[1:len(value) - 1].replace("\"", "\\\"") + "\""
    has_2_quote = '"' in value
    has_1_quote = "'" in value
    if has_1_quote and not has_2_quote:
        return '"{}"'.format(value)
    if has_2_quote and not has_1_quote:
        return "'{}'".format(value)
    return '"{}"'.format(value.replace("'", "\\'"))


def create_connection():
    persistence = MysqlUtil(host=mysql_host, user=mysql_user, pss=mysql_password,
                            db=mysql_db, port=mysql_port)
    return persistence


class MysqlUtil:

    def __init__(self, host='localhost', user='root', pss='root', db='qcc', port=3306):
        self.db_host = host
        self.db_user = user
        self.db_pass = pss
        self.db_name = db
        self.db_port = port
        try:
            self.db_connection = pymysql.connect(host=self.db_host, user=self.db_user, password=self.db_pass,
                                                 database=self.db_name, port=self.db_port, autocommit=True)
        except pymysql.Error as e:
            printInfo("数据库连接失败：" + str(e))
        self.cursor = self.db_connection.cursor()

    def test(self):
        self.cursor.execute("SELECT VERSION()")
        # 使用 fetchone() 方法获取一条数据
        data = self.cursor.fetchone()
        printInfo("Database version : %s " % data)

    def execute(self, sql):
        printInfo("执行sql：" + sql)
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        printDebug("结果：")
        printDebug(result)
        return result

    def close(self):
        if self.db_connection:
            self.db_connection.close()
            printInfo('关闭数据库连接....')


if __name__ == '__main__':
    # mysql = MysqlUtil(host='localhost', user='root', pss='root', db='qcc')
    # mysql.execute("show databases")
    # mysql.close()
    a = "\"123\"124\""
    print("\"" + a[1:len(a) - 1].replace("\"", "\\\"") + "\"")

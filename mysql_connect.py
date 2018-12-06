import pymysql,json
from transfer_to_json import run
source_web = "https://weibo.com/2188971353/H1BHS3jyo"

host = "202.120.37.116"
port = 20136
username = "root"
passwd = "mcontent2018"
dbname = "spreadLink"
json_result_str = run(source_web)

db = pymysql.connect(host=host,
                     port=port,
                     user=username,
                     password=passwd,
                     db=dbname)

with db.cursor() as cursor:
    # sql = "select * from link where linkType=2"
    # cursor.execute(sql)
    #
    # sql_result = cursor.fetchall()

    sql = "insert into link " \
          "values(%s,%s,%s)" % ('7',json_result_str,'1')
    cursor.execute(sql)
    sql_result = cursor.fetchall()
    print(sql_result)

db.close()
# sql_result_text = json.loads(sql_result[1][0])
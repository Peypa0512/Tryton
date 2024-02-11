import psycopg2

conn = psycopg2.connect(database='cars_db',
                        user='tryton',
                        password='Admin,1$',
                        host='localhost', port='5432')

cur = conn.cursor()

sql = 'Select * from taller_modelo'
cur.execute(sql)
datos = cur.fetchall()

for dato in datos:
    print(dato)
cur.close()

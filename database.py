import psycopg2
conn = psycopg2.connect(
    host="ec2-3-232-13-123.compute-1.amazonaws.com",
    database="dhp4uj4dit0ef",
    user="qlpuwryuympbci",
    password="5f3d75c0d1bda122157793cbcbc8d6074492a29dc754960ba2fe6d40bc260079")

cur = conn.cursor()
# print('PostgreSQL database version:')
# cur.execute('SELECT version()')
# db_version = cur.fetchone()
# print(db_version)

def student_list():
    query = 'SELECT student_name FROM student_attributes'
    cur.execute(query)
    exec = cur.fetchall()
    return list(map(lambda x: x[0], exec))

def get_password():
    query = 'SELECT password FROM login'
    cur.execute(query)
    exec = cur.fetchone()
    return exec[0]

def update_password(password):
    query = 'UPDATE login SET password = \''+password+'\' WHERE password = \''+get_password()+'\''
    print(query)
    cur.execute(query)
    conn.commit()
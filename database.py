import psycopg2
from datetime import datetime

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


#------------------Student_attributes-----------------------#

#Getters
def get_email(name):
    query = 'SELECT email FROM student_attributes WHERE student_name = \'' + name + '\''
    cur.execute(query)
    exec = cur.fetchone()
    return exec[0]

def get_necessary_minutes(name):
    query = 'SELECT necessary_minutes FROM student_attributes WHERE student_name = \'' + name + '\''
    cur.execute(query)
    exec = cur.fetchone()
    return exec[0]

def get_unconfirmed_minutes(name):
    query = 'SELECT unconfirmed_minutes FROM student_attributes WHERE student_name = \'' + name + '\''
    cur.execute(query)
    exec = cur.fetchone()
    return exec[0]

def get_confirmed_minutes(name):
    query = 'SELECT confirmed_minutes FROM student_attributes WHERE student_name = \'' + name + '\''
    cur.execute(query)
    exec = cur.fetchone()
    return exec[0]

def get_exempt(name):
    query = 'SELECT exempt FROM student_attributes WHERE student_name = \'' + name + '\''
    cur.execute(query)
    exec = cur.fetchone()
    return exec[0]

def student_list():
    query = 'SELECT student_name FROM student_attributes'
    cur.execute(query)
    exec = cur.fetchall()
    return list(map(lambda x: x[0], exec))

def get_meeting(name):
    query = 'SELECT meeting FROM student_attributes WHERE student_name = \'' + name + '\''
    cur.execute(query)
    exec = cur.fetchone()
    return exec[0]

#Setters
def add_student(name):
    query = "INSERT INTO student_attributes (student_name) VALUES (%s)"
    cur.execute(query, [name])
    conn.commit()

def change_name(old_name, new_name):
    query = 'UPDATE student_attributes SET student_name = \'' + new_name + '\' WHERE student_name = \'' + old_name + '\''
    cur.execute(query)
    conn.commit()

def change_email_from_name(name, email):
    query = 'UPDATE student_attributes SET email = \'' + email + '\' WHERE student_name = \'' + name + '\''
    cur.execute(query)
    conn.commit()

def toggle_exempt_from_name(name):
    query = 'UPDATE student_attributes SET exempt = NOT exempt WHERE student_name = \'' + name + '\''
    cur.execute(query)
    conn.commit()

def toggle_meeting_from_name(name):
    query = 'UPDATE student_attributes SET meeting = NOT meeting WHERE student_name = \'' + name + '\''
    cur.execute(query)
    conn.commit()

def change_necessary_minutes(name, minutes):
    query = 'UPDATE student_attributes SET necessary_minutes = ' + str(minutes) + ' WHERE student_name = \'' + name + '\''
    cur.execute(query)
    conn.commit()

def add_unconfirmed_minutes(name, minutes):
    minutes+=get_unconfirmed_minutes(name)
    query = 'UPDATE student_attributes SET unconfirmed_minutes = ' + str(minutes) + ' WHERE student_name = \'' + name + '\''
    cur.execute(query)
    conn.commit()

def add_confirmed_minutes(name, minutes):
    minutes += get_confirmed_minutes(name)
    query = 'UPDATE student_attributes SET confirmed_minutes = ' + str(minutes) + ' WHERE student_name = \'' + name + '\''
    cur.execute(query)
    conn.commit()

#Login
def get_password():
    query = 'SELECT password FROM login'
    cur.execute(query)
    exec = cur.fetchone()
    return exec[0]

def update_password(password):
    query = 'UPDATE login SET password = \''+password+'\' WHERE password = \''+get_password()+'\''
    cur.execute(query)
    conn.commit()




#------------------student_fairs-----------------------#
#Getters
def fairs_list():
    query = 'SELECT fair FROM student_fairs'
    cur.execute(query)
    exec = cur.fetchall()
    return list(set(map(lambda x: x[0], exec)))

def students_from_fair(fair):
    query = 'SELECT student_name FROM student_fairs WHERE fair = \'' + fair + '\''
    cur.execute(query)
    exec = cur.fetchall()
    return list(map(lambda x: x[0], exec))

def get_fairs(name):
    query = 'SELECT fair FROM student_fairs WHERE student_name = \'' + name + '\''
    cur.execute(query)
    exec = cur.fetchall()
    return len(list(map(lambda x: x[0], exec)))

#Setters
def add_fair(fair):
    query = "INSERT INTO student_fairs (fair) VALUES (%s)"
    cur.execute(query, [fair])
    conn.commit()

def delete_fair(fair):
    query = "DELETE FROM student_fairs WHERE fair = \'" + fair + '\''
    cur.execute(query)
    conn.commit()


def add_student_to_fair(name, fair):
    query = "INSERT INTO student_fairs (student_name, fair) VALUES (%s, %s)"
    cur.execute(query, (name, fair))
    conn.commit()

def delete_student_fair(name, fair):
    query = "DELETE FROM student_fairs WHERE student_name = \'" + name + '\' AND fair = \'' + fair + '\''
    cur.execute(query)
    conn.commit()

#------------------student_entries-----------------------#
#Getters
def get_student_names_without_end():
    query = 'SELECT student_name FROM student_entries WHERE end_time IS NULL'
    cur.execute(query)
    exec = cur.fetchall()
    return list(map(lambda x: x[0], exec))

def get_student_start_with_end(name):
    query = 'SELECT start_time FROM student_entries WHERE student_name = \'' + name + '\' AND end_time IS NOT NULL'
    cur.execute(query)
    exec = cur.fetchall()
    return list(map(lambda x: x[0], exec))

def get_student_end(name):
    query = 'SELECT end_time FROM student_entries WHERE student_name = \'' + name + '\' AND end_time IS NOT NULL'
    cur.execute(query)
    exec = cur.fetchall()
    return list(map(lambda x: x[0], exec))

def get_student_end_with_start(name, start):
    query = 'SELECT end_time FROM student_entries WHERE student_name = \'' + name + '\' AND start_time = \'' + str(start) + '\' AND end_time IS NOT NULL'
    cur.execute(query)
    exec = cur.fetchone()
    return exec[0]

def get_unconfirmed_entries():
    query = 'SELECT student_name FROM student_entries WHERE end_time IS NOT NULL'
    cur.execute(query)
    exec = cur.fetchall()
    l = []
    names = list(set(map(lambda x: x[0], exec)))
    for name in names:
        starts = get_student_start_with_end(name)
        ends = get_student_end(name)
        if(starts == None):
            continue
        for i in range(0, len(starts)):
            l.append(name + " " + str(datetime.fromtimestamp(starts[i])) + "-->" + str(datetime.fromtimestamp(ends[i]))[11:19])
    return l

def get_start_time(name):
    query = "SELECT start_time FROM student_entries WHERE student_name = \'" + name + '\' AND end_time IS NULL'
    cur.execute(query)
    exec = cur.fetchone()
    return exec[0]

#Setters
def add_student_start(name, time):
    query = "INSERT INTO student_entries (student_name, start_time) VALUES (%s, %s)"
    cur.execute(query, (name, time))
    conn.commit()

def update_student_end(name, time):
    query = 'UPDATE student_entries SET end_time = \'' + str(time) + '\' WHERE student_name = \'' + name + '\' AND end_time IS NULL'
    cur.execute(query, (name, time))
    conn.commit()

def delete_minute_zero(name):
    query = 'DELETE FROM student_entries WHERE student_name = \'' + name + '\' AND end_time IS NULL'
    cur.execute(query)
    conn.commit()

def delete_start_time(name, start):
    query = 'DELETE FROM student_entries WHERE student_name = \'' + name + '\' AND start_time = \'' + str(start) + '\''
    cur.execute(query)
    conn.commit()

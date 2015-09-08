import sqlite3
import os.path
from os import listdir, getcwd
import Image

def create_or_open_db(db_file):
    db_is_new = not os.path.exists(db_file)
    conn = sqlite3.connect(db_file)
    # if db_is_new:
    print 'Creating schema'
    sql = '''create table if not exists PICTURE(
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    PICTURE BLOB,
    TYPE TEXT,
    FILE_NAME TEXT);'''
    conn.execute(sql) # shortcut for conn.cursor().execute(sql)
    # else:
    #     print 'Schema exists\n'
    return conn

def insert_picture(conn, picture_file):
    with open(picture_file, 'rb') as input_file:
        ablob = input_file.read()
        base=os.path.basename(picture_file)
        afile, ext = os.path.splitext(base)
        print afile, ext
        sql = '''INSERT INTO PICTURE
        (PICTURE, TYPE, FILE_NAME)
        VALUES(?, ?, ?);'''
        conn.execute(sql,[sqlite3.Binary(ablob), ext, 'afile']) 
        conn.commit()
    print 'insert_picture'

conn = create_or_open_db('mydatabase.db')
insert_picture(conn, 'map.jpg')

picture_file = "./map.jpg"
insert_picture(conn, picture_file)
conn.close()


def extract_picture(cursor, picture_id):
    sql = "SELECT PICTURE, TYPE, FILE_NAME FROM PICTURE WHERE id = :id"
    param = {'id': picture_id}
    cursor.execute(sql, param)
    ablob, ext, afile = cursor.fetchone()
    filename = afile + ext
    with open(filename, 'wb') as output_file:
        output_file.write(ablob)
    print filename
    return ablob

conn = create_or_open_db('mydatabase.db')
cur = conn.cursor()
filename = extract_picture(cur, 1)
cur.close()
conn.close()

# print filename
import Tkinter 
import Image, ImageTk
from StringIO import StringIO

# open a SPIDER image and convert to byte
format
im = Image.open(StringIO(filename))

root = Tkinter.Tk()  
# A root window for displaying objects

 # Convert the Image object into a TkPhoto 
object
tkimage = ImageTk.PhotoImage(im)

Tkinter.Label(root, image=tkimage).pack() 
# Put it in the display window

root.mainloop() # Start the GUI
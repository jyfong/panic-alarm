import dataset
import sqlite3
import sqlalchemy 
# from sqlalchemy.sql import 

file = open('map.jpg')
map = sqlite3.Binary(file.read())

query = "INSERT INTO File (name, bin) VALUES ('image', %s)" % [buffer(file)]

db = dataset.connect('sqlite:///:memory:')

table = db['File']

table.create_column('name', sqlalchemy.String)
table.create_column('bin', sqlalchemy.BLOB)

db.query(query)
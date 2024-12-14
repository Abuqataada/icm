import sqlite3

# Connect to the database
conn = sqlite3.connect('instance/users.db')

# Create a cursor object
cursor = conn.cursor()

# Add a school
#school_name = 'Admin School'  # Replace with the actual school name
##cursor.execute("INSERT INTO schools (name) VALUES (?);", (school_name,))
schools = conn.execute('SELECT * FROM school').fetchall()
# Commit the changes and close the connection
#conn.commit()
conn.close()
print(schools)
print({'schools': [dict(school) for school in schools]})
#print(f'School "{school_name}" added successfully.')

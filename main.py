
import mysql.connector

# Connect to MySQL database
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="DS_db"
)

cursor = conn.cursor()

# Get employee details
id = int(input("Enter Employee ID: "))
name = input("Enter Employee Name: ")
age = int(input("Enter Employee Age: "))
salary = int(input("Enter Employee Salary: "))
design = input("Enter Employee Designation: ")

# Insert employee record
sql = """
INSERT INTO Emp (ID, name, age, salary, design)
VALUES (%s, %s, %s, %s, %s)
"""

values = (id, name, age, salary, design)

try:
    cursor.execute(sql, values)
    conn.commit()

    print("\nEmployee inserted successfully!")

    # Display all employee records
    cursor.execute("SELECT * FROM Emp")
    records = cursor.fetchall()

    print("\n--- Employee Records ---")
    for row in records:
        print(row)

except mysql.connector.Error as err:
    conn.rollback()
    print("Error:", err)

finally:
    cursor.close()
    conn.close()

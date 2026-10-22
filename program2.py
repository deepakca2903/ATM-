
import mysql.connector

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="DS_db"
)

cursor = conn.cursor()


# ADD EMPLOYEE
def add_employee():
    try:
        emp_id = int(input("Enter Employee ID: "))
        name = input("Enter Employee Name: ")
        age = int(input("Enter Age: "))
        salary = int(input("Enter Salary: "))
        design = input("Enter Designation: ")

        sql = """
        INSERT INTO Emp (ID, name, age, salary, design)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (emp_id, name, age, salary, design)

        cursor.execute(sql, values)
        conn.commit()

        print("Employee added successfully!")

    except (ValueError, mysql.connector.Error) as e:
        conn.rollback()
        print("Error:", e)


# DISPLAY EMPLOYEES
def display_employees():
    cursor.execute("SELECT * FROM Emp")
    records = cursor.fetchall()

    if not records:
        print("No employee records found.")
        return

    print("\n--- Employee Records ---")
    print("-" * 75)
    print(f"{'ID':<8}{'Name':<15}{'Age':<8}{'Salary':<12}{'Designation'}")
    print("-" * 75)

    for row in records:
        print(f"{row[0]:<8}{row[1]:<15}{row[2]:<8}"
              f"{row[3]:<12}{row[4]}")

    print("-" * 75)


# UPDATE EMPLOYEE
def update_employee():
    try:
        emp_id = int(input("Enter Employee ID to update: "))

        cursor.execute("SELECT * FROM Emp WHERE ID = %s", (emp_id,))
        if cursor.fetchone() is None:
            print("Employee not found!")
            return

        name = input("Enter new name: ")
        age = int(input("Enter new age: "))
        salary = int(input("Enter new salary: "))
        design = input("Enter new designation: ")

        sql = """
        UPDATE Emp
        SET name = %s, age = %s, salary = %s, design = %s
        WHERE ID = %s
        """
        values = (name, age, salary, design, emp_id)

        cursor.execute(sql, values)
        conn.commit()

        print("Employee updated successfully!")

    except (ValueError, mysql.connector.Error) as e:
        conn.rollback()
        print("Error:", e)


# DELETE EMPLOYEE
def delete_employee():
    try:
        emp_id = int(input("Enter Employee ID to delete: "))

        cursor.execute("DELETE FROM Emp WHERE ID = %s", (emp_id,))
        conn.commit()

        if cursor.rowcount > 0:
            print("Employee deleted successfully!")
        else:
            print("Employee not found!")

    except (ValueError, mysql.connector.Error) as e:
        conn.rollback()
        print("Error:", e)


# MAIN MENU
try:
    while True:
        print("\n===== EMPLOYEE MANAGEMENT SYSTEM =====")
        print("1. Add Employee")
        print("2. Display Employees")
        print("3. Update Employee")
        print("4. Delete Employee")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            add_employee()

        elif choice == "2":
            display_employees()

        elif choice == "3":
            update_employee()

        elif choice == "4":
            delete_employee()

        elif choice == "5":
            print("Exiting program...")
            break

        else:
            print("Invalid choice! Please enter 1 to 5.")

finally:
    cursor.close()
    conn.close()
    print("MySQL connection closed.")

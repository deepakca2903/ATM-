
import mysql.connector

# Connect to MySQL database
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="DS_db"
)

cursor = conn.cursor()


# 1. ADD EMPLOYEE
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
        cursor.execute(sql, (emp_id, name, age, salary, design))
        conn.commit()
        print("Employee added successfully!")

    except (ValueError, mysql.connector.Error) as e:
        conn.rollback()
        print("Error:", e)


# 2. DISPLAY ALL EMPLOYEES
def display_employees():
    cursor.execute("SELECT * FROM Emp ORDER BY ID")
    records = cursor.fetchall()

    if not records:
        print("No employee records found.")
        return

    print("\n{:<8} {:<20} {:<8} {:<12} {:<20}".format(
        "ID", "Name", "Age", "Salary", "Designation"
    ))
    print("-" * 70)

    for row in records:
        print("{:<8} {:<20} {:<8} {:<12} {:<20}".format(
            row[0], row[1], row[2], row[3], row[4]
        ))


# 3. UPDATE EMPLOYEE
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
        cursor.execute(sql, (name, age, salary, design, emp_id))
        conn.commit()

        print("Employee updated successfully!")

    except (ValueError, mysql.connector.Error) as e:
        conn.rollback()
        print("Error:", e)


# 4. DELETE EMPLOYEE
def delete_employee():
    try:
        emp_id = int(input("Enter Employee ID to delete: "))

        cursor.execute("DELETE FROM Emp WHERE ID = %s", (emp_id,))
        deleted = cursor.rowcount
        conn.commit()

        if deleted > 0:
            print("Employee deleted successfully!")
        else:
            print("Employee not found!")

    except (ValueError, mysql.connector.Error) as e:
        conn.rollback()
        print("Error:", e)


# 5. SEARCH EMPLOYEE BY ID
def search_by_id():
    try:
        emp_id = int(input("Enter Employee ID: "))
        cursor.execute("SELECT * FROM Emp WHERE ID = %s", (emp_id,))
        record = cursor.fetchone()

        if record:
            print("Employee details:", record)
        else:
            print("Employee not found!")

    except ValueError:
        print("Please enter a valid numeric ID.")


# 6. SEARCH EMPLOYEE BY NAME
def search_by_name():
    name = input("Enter employee name: ")

    cursor.execute(
        "SELECT * FROM Emp WHERE name LIKE %s",
        (f"%{name}%",)
    )
    records = cursor.fetchall()

    if records:
        for row in records:
            print(row)
    else:
        print("Employee not found!")


# 7. SEARCH BY DESIGNATION
def by_designation():
    design = input("Enter designation: ")

    cursor.execute(
        "SELECT * FROM Emp WHERE design LIKE %s",
        (f"%{design}%",)
    )
    records = cursor.fetchall()

    if records:
        for row in records:
            print(row)
    else:
        print("No employees found for this designation.")


# 8. EMPLOYEES WITH SALARY ABOVE AN AMOUNT
def salary_above():
    try:
        amount = int(input("Enter minimum salary: "))

        cursor.execute(
            "SELECT * FROM Emp WHERE salary > %s ORDER BY salary DESC",
            (amount,)
        )
        records = cursor.fetchall()

        if records:
            for row in records:
                print(row)
        else:
            print("No employees found above this salary.")

    except ValueError:
        print("Enter a valid salary.")


# 9. SORT EMPLOYEES BY SALARY
def sort_by_salary():
    cursor.execute("SELECT * FROM Emp ORDER BY salary DESC")
    records = cursor.fetchall()

    print("\nEmployees sorted by salary (highest first):")
    for row in records:
        print(row)


# 10. COUNT TOTAL EMPLOYEES
def employee_count():
    cursor.execute("SELECT COUNT(*) FROM Emp")
    count = cursor.fetchone()[0]
    print("Total employees:", count)


# 11. HIGHEST-PAID EMPLOYEE
def highest_paid():
    cursor.execute(
        "SELECT * FROM Emp ORDER BY salary DESC LIMIT 1"
    )
    record = cursor.fetchone()

    if record:
        print("Highest-paid employee:", record)
    else:
        print("No employees found.")


# 12. AVERAGE SALARY
def average_salary():
    cursor.execute("SELECT AVG(salary) FROM Emp")
    result = cursor.fetchone()[0]

    if result is not None:
        print("Average salary:", round(result, 2))
    else:
        print("No salary records available.")


# 13. SEARCH EMPLOYEES BY AGE
def by_age():
    try:
        age = int(input("Enter age: "))

        cursor.execute("SELECT * FROM Emp WHERE age = %s", (age,))
        records = cursor.fetchall()

        if records:
            for row in records:
                print(row)
        else:
            print("No employees found at this age.")

    except ValueError:
        print("Enter a valid age.")


# 14. TOTAL SALARY EXPENSE
def total_salary_expense():
    cursor.execute("SELECT SUM(salary) FROM Emp")
    total = cursor.fetchone()[0]

    print("Total salary expense:", total if total is not None else 0)


# MAIN MENU
try:
    while True:
        print("""
========== EMPLOYEE MANAGEMENT SYSTEM ==========
1.  Add Employee
2.  Display All Employees
3.  Update Employee
4.  Delete Employee
5.  Search Employee by ID
6.  Search Employee by Name
7.  Search by Designation
8.  Employees with Salary Above Amount
9.  Sort Employees by Salary
10. Count Total Employees
11. Highest-Paid Employee
12. Average Salary
13. Search Employees by Age
14. Total Salary Expense
15. Exit
================================================
""")

        choice = input("Enter your choice (1-15): ")

        try:
            if choice == "1":
                add_employee()
            elif choice == "2":
                display_employees()
            elif choice == "3":
                update_employee()
            elif choice == "4":
                delete_employee()
            elif choice == "5":
                search_by_id()
            elif choice == "6":
                search_by_name()
            elif choice == "7":
                by_designation()
            elif choice == "8":
                salary_above()
            elif choice == "9":
                sort_by_salary()
            elif choice == "10":
                employee_count()
            elif choice == "11":
                highest_paid()
            elif choice == "12":
                average_salary()
            elif choice == "13":
                by_age()
            elif choice == "14":
                total_salary_expense()
            elif choice == "15":
                print("Thank you! Exiting program.")
                break
            else:
                print("Invalid choice! Enter a number from 1 to 15.")

        except mysql.connector.Error as e:
            conn.rollback()
            print("Database error:", e)

finally:
    cursor.close()
    conn.close()
    print("MySQL connection closed.")

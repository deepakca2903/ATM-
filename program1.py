
employees = []

while True:
    print("\n===== EMPLOYEE MANAGEMENT SYSTEM =====")
    print("1. Add Employee")
    print("2. Display Employees")
    print("3. Update Employee")
    print("4. Delete Employee")
    print("5. Exit")

    choice = int(input("Enter your choice: "))

    if choice == 1:
        emp_id = int(input("Enter Employee ID: "))
        name = input("Enter Employee Name: ")
        salary = float(input("Enter Salary: "))
        designation = input("Enter Designation: ")

        employee = {
            "id": emp_id,
            "name": name,
            "salary": salary,
            "designation": designation
        }

        employees.append(employee)
        print("Employee added successfully!")

    elif choice == 2:
        if len(employees) == 0:
            print("No employee records found.")
        else:
            print("\n--- Employee Details ---")

            for emp in employees:
                print("ID:", emp["id"])
                print("Name:", emp["name"])
                print("Salary:", emp["salary"])
                print("Designation:", emp["designation"])
                print("----------------------")

    elif choice == 3:
        emp_id = int(input("Enter Employee ID to update: "))

        for emp in employees:
            if emp["id"] == emp_id:
                emp["name"] = input("Enter New Name: ")
                emp["salary"] = float(input("Enter New Salary: "))
                emp["designation"] = input("Enter New Designation: ")

                print("Employee updated successfully!")
                break
        else:
            print("Employee ID not found.")

    elif choice == 4:
        emp_id = int(input("Enter Employee ID to delete: "))

        for emp in employees:
            if emp["id"] == emp_id:
                employees.remove(emp)
                print("Employee deleted successfully!")
                break
        else:
            print("Employee ID not found.")

    elif choice == 5:
        print("Exiting Employee Management System.")
        break

    else:
        print("Invalid choice! Please enter 1 to 5.")

import csv
import random

def generate_csv():
    # Names for Faculty
    faculty_names = [
        "Dr. Rajesh Kumar", "Prof. Sneha Patil", "Dr. Amit Sharma", "Prof. Neha Gupta",
        "Dr. Vikram Singh", "Prof. Priya Desai", "Dr. Manoj Joshi", "Prof. Kavita Iyer",
        "Dr. Suresh Menon", "Prof. Anjali Verma", "Dr. Rohan Das", "Prof. Meera Reddy"
    ]
    
    # 50 Unique Indian Names for Students
    unique_student_names = [
        "Aarav Sharma", "Vihaan Verma", "Vivaan Gupta", "Ananya Patil", "Diya Desai", 
        "Advik Joshi", "Kavya Iyer", "Ishaan Menon", "Riya Reddy", "Aarush Das", 
        "Fatima Sheikh", "Arjun Singh", "Sara Khan", "Kabir Kumar", "Meher Chopra", 
        "Rohan Bose", "Sanya Nair", "Dhruv Rao", "Zara Garg", "Aryan Agarwal", 
        "Isha Mehta", "Rahul Jain", "Pooja Trivedi", "Vikram Chawla", "Neha Bhat", 
        "Karan Kulkarni", "Sneha Pande", "Aditya Bhatia", "Shruti Sinha", "Ravi Kapoor", 
        "Anjali Malhotra", "Sanjay Khanna", "Kiran Ahuja", "Amit Saxena", "Nisha Thakur", 
        "Raj Chatterjee", "Preeti Soni", "Sunil Mistry", "Asha Pillai", "Vijay Shenoy",
        "Rakesh Tiwari", "Rutuja Kadam", "Harsh Vardhan", "Smriti Irani", "Karthik Natarajan",
        "Jyoti Basu", "Gaurav shukla", "Divya Agrawal", "Manish Pandey", "Priyanka Yadav"
    ]
    
    courses = {
        "AI": {
            "name": "Artificial Intelligence",
            "code": "AI",
            "subjects": ["Python", "Machine Learning", "Deep Learning", "NLP"],
            "student_count": 10,
            "prn_start": 2001
        },
        "BDA": {
            "name": "Big Data Analytics",
            "code": "BDA",
            "subjects": ["Java", "Python", "Data Analytics", "Machine Learning"],
            "student_count": 20,
            "prn_start": 3001
        },
        "AC": {
            "name": "Advanced Computing",
            "code": "AC",
            "subjects": ["Java", "C++", "Operating Systems", "Web Development"],
            "student_count": 20,
            "prn_start": 4001
        }
    }
    
    csv_file = "/Users/shubham/Desktop/demo_upload_multi.csv"
    
    with open(csv_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Course_Name", "Course_Code", "Subject_Name", "Faculty_Name", "Faculty_Email", "Student_Name", "Student_PRN", "Student_Email"])
        
        fac_idx = 0
        student_idx = 0
        
        for course_code, cdata in courses.items():
            # Generate rows for Faculty (1 per subject)
            for subj in cdata["subjects"]:
                fac_name = faculty_names[fac_idx]
                # Email format: firstname.lastname@gmail.com
                fac_email = f"{fac_name.replace('Dr. ', '').replace('Prof. ', '').replace(' ', '.').lower()}@gmail.com"
                fac_idx += 1
                
                # Faculty row
                writer.writerow([cdata["name"], cdata["code"], subj, fac_name, fac_email, "", "", ""])
                
            # Generate rows for Students
            for i in range(cdata["student_count"]):
                prn = str(cdata["prn_start"] + i)
                st_name = unique_student_names[student_idx]
                student_idx += 1
                
                parts = st_name.split()
                st_fname = parts[0]
                st_lname = parts[1] if len(parts) > 1 else ""
                
                st_email = f"{st_fname.lower()}.{st_lname.lower()}{prn}@gmail.com"
                
                # Student row (Subject and Faculty are blank)
                writer.writerow([cdata["name"], cdata["code"], "", "", "", st_name, prn, st_email])
                
    print(f"Generated {csv_file}")

if __name__ == "__main__":
    generate_csv()

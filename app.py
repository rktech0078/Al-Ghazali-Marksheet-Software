import streamlit as st
import json
import os
import pandas as pd
import base64
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from datetime import datetime
from io import BytesIO

st.set_page_config( page_icon="📜", page_title="Al-Ghazali Marksheet Software" )
# --- Function to Load Data from JSON ---
def load_data():
    if os.path.exists('students_data.json'):
        with open('students_data.json', 'r') as file:
            return json.load(file)
    return []

# --- Function to Save Data to JSON ---
def save_data():
    with open('students_data.json', 'w') as file:
        json.dump(st.session_state.students_data, file, indent=4)

# --- Function to Calculate Subject-wise Percentage, Grade and Remarks ---
def calculate_subject_result(mark, total_marks):
    percentage = (mark / total_marks) * 100
    
    if percentage >= 80:
        grade = 'A+'
        remarks = "EXCELLENT"
    elif percentage >= 70:
        grade = 'A'
        remarks = "GOOD"
    elif percentage >= 60:
        grade = 'B'
        remarks = "AVERAGE"
    elif percentage >= 50:
        grade = 'C'
        remarks = "POOR"
    else:
        grade = 'F'
        remarks = "NEEDS TO WORK HARD"
        
    return percentage, grade, remarks

# --- Function to Calculate Total, Percentage, Grade ---
def calculate_result(marks, total_marks):
    total = sum(marks)
    percentage = (total / (len(marks) * total_marks)) * 100

    if percentage >= 80:
        grade = 'A+'
    elif percentage >= 70:
        grade = 'A'
    elif percentage >= 60:
        grade = 'B'
    elif percentage >= 50:
        grade = 'C'
    else:
        grade = 'F'

    return total, percentage, grade


# --- Function to Get Position in Class ---
def get_position(student_percentage, all_students, class_name):
    # Filter students by class
    class_students = [s for s in all_students if s.get('class_name') == class_name]
    
    # Sort by percentage in descending order
    sorted_students = sorted(class_students, key=lambda x: x['percentage'], reverse=True)
    
    # Find position
    for i, s in enumerate(sorted_students):
        if s['percentage'] == student_percentage:
            return i + 1
    
    return "N/A"

# --- Enhanced PDF Generation Function for Individual Marksheets ---
def generate_individual_pdfs(selected_students, include_combined=True):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    width, height = A4
    
    # Get all students to calculate positions
    all_students = st.session_state.students_data
    
    for student in selected_students:
        # Calculate subject-wise results
        subject_results = []
        for mark in student['marks']:
            percentage, grade, remarks = calculate_subject_result(mark, st.session_state.total_marks_per_subject)
            subject_results.append({
                'percentage': percentage,
                'grade': grade,
                'remarks': remarks
            })
        
        # Total possible marks
        total_possible = len(student['marks']) * st.session_state.total_marks_per_subject
        
        # Get position in class
        position = get_position(student['percentage'], all_students, student.get('class_name', 'N/A'))
        
        # -------------------- HEADER --------------------
        p.setFont("Helvetica-Bold", 18)
        p.setFillColor(colors.HexColor("#0076BE"))
        p.drawCentredString(width / 2, height - 50, "Al Ghazali High School")

        p.setFont("Helvetica", 10)
        p.setFillColor(colors.black)
        p.drawCentredString(width / 2, height - 68, "36/B, Landhi, Karachi, Near Daru-l-uloom Karachi")

        p.setFont("Helvetica-Bold", 14)
        p.setFillColor(colors.green)
        p.drawCentredString(width / 2, height - 90, f"Marksheet For {datetime.now().year} (First Test)")

        # --- Optional Logo Placeholder ---
        try:
            # Left logo
            left_logo_path = "Al Ghazali Logo.jpg"
            p.drawImage(
                ImageReader(left_logo_path),
                40,  # x-position
                height - 100,  # y-position
                width=60,
                height=60,
                preserveAspectRatio=True,
                mask='auto'
            )

            # Right logo
            right_logo_path = "Al Ghazali Logo1.jpg"
            p.drawImage(
                ImageReader(right_logo_path),
                width - 100,  # x-position
                height - 100,  # y-position
                width=60,
                height=60,
                preserveAspectRatio=True,
                mask='auto'
            )
        except:
            # If logo files don't exist, create placeholders
            p.setStrokeColor(colors.gray)
            p.ellipse(40, height - 100, 100, height - 40, stroke=1, fill=0)
            p.ellipse(width - 100, height - 100, width - 40, height - 40, stroke=1, fill=0)
        
        # -------------------- STUDENT INFO --------------------
        student_info_top = height - 130
        p.setStrokeColor(colors.HexColor("#0076BE"))
        p.setFillColor(colors.HexColor("#B8E1FF"))
        p.roundRect(40, student_info_top - 60, width - 80, 60, radius=2, fill=1)

        p.setFillColor(colors.black)
        p.setFont("Helvetica-Bold", 9)
        p.drawString(50, student_info_top - 21, "STUDENT'S NAME:")
        p.drawString(50, student_info_top - 44, "FATHER'S NAME:")
        p.setFont("Helvetica-Bold", 11)
        p.drawString(450, student_info_top - 21, "Roll NO:")
        p.drawString(450, student_info_top - 44, "Class:")

        # Add student information
        p.setFont("Helvetica", 10)
        p.drawString(140, student_info_top - 21, student['name'])
        # If father's name is not available, use placeholder
        father_name = student.get('father_name', "")
        p.drawString(140, student_info_top - 44, father_name)
        p.setFont("Helvetica", 12)
        p.drawString(500, student_info_top - 21, student['roll_no'])
        p.drawString(500, student_info_top - 44, student.get('class_name', 'N/A'))

        # -------------------- MARKS TABLE --------------------
        subjects = st.session_state.subjects
        y_table = student_info_top - 100
        row_height = 25
        num_rows = len(subjects) + 1  # +1 for header

        # Column positions (adjusted for better spacing)
        x_left = 40
        x_right = width - 40
        col_xs = [x_left, 70, 150, 220, 290, 370, 450, x_right]

        # Draw horizontal lines (rows)
        for i in range(num_rows + 1):
            y = y_table - (i * row_height)
            p.line(x_left, y, x_right, y)

        # Draw vertical lines (columns)
        for x in col_xs:
            p.line(x, y_table, x, y_table - (num_rows * row_height))

        # Header row
        p.setFillColor(colors.yellow)
        p.rect(x_left, y_table - row_height, x_right - x_left, row_height, fill=1)
        p.setFillColor(colors.black)
        p.setFont("Helvetica-Bold", 9)

        headers = ["S/N", "SUBJECT", "TOTAL", "OBTAINED", "PERCENTAGE", "GRADE", "REMARKS"]
        col_centers = [(col_xs[i] + col_xs[i + 1]) / 2 for i in range(len(col_xs) - 1)]

        for i, head in enumerate(headers):
            p.drawCentredString(col_centers[i], y_table - row_height + 7, head)

        # Subject rows
        p.setFont("Helvetica", 9)
        for i, (subject, mark, result) in enumerate(zip(subjects, student['marks'], subject_results)):
            y = y_table - ((i + 2) * row_height)
            # Convert subject name to uppercase as required
            subject_uppercase = subject.upper()
            row_values = [
                str(i + 1), 
                subject_uppercase, 
                str(st.session_state.total_marks_per_subject), 
                str(mark), 
                f"{result['percentage']:.2f}%", 
                result['grade'], 
                result['remarks']
            ]
            for j, value in enumerate(row_values):
                # If it's a long subject name, handle text wrapping
                if j == 1 and len(value) > 15:  # For subject column
                    p.drawString(col_xs[j] + 2, y + 12, value[:15])
                    p.drawString(col_xs[j] + 2, y + 2, value[15:30])
                else:
                    p.drawCentredString(col_centers[j], y + 7, value)

        # -------------------- SUMMARY --------------------
        summary_y = y_table - (num_rows * row_height) - 80
        box_x = 40
        box_width = 220
        box_height = 90

        # Light blue background for the summary box
        p.setFillColor(colors.HexColor("#EAF6FF"))
        p.setStrokeColor(colors.HexColor("#0076BE"))
        p.roundRect(box_x, summary_y - 44, box_width + 15, box_height + 10, radius=0, fill=1)

        # Yellow rounded label for "SUMMARY:"
        p.setFillColor(colors.yellow)
        p.roundRect(box_x + 15, summary_y + 45, box_width - 15, 25, radius=0, fill=1, stroke=0)

        # Text: SUMMARY title
        p.setFillColor(colors.black)
        p.setFont("Helvetica-Bold", 11)
        p.drawString(box_x + 73, summary_y + 54, "SUMMARY")

        # Text: Summary details
        p.setFont("Helvetica", 9)
        p.drawString(box_x + 15, summary_y + 20, f"TOTAL MARKS: {total_possible}")
        p.drawString(box_x + 15, summary_y + 5, f"MARKS OBTAINED: {student['total']}")
        p.drawString(box_x + 15, summary_y - 10, f"GRADE: {student['grade']}")
        p.drawString(box_x + 15, summary_y - 25, f"PERCENTAGE: {student['percentage']:.2f}%")
        
        # Add position info with highlighting
        position_text = f"POSITION: {position}"
        p.drawString(box_x + 15, summary_y - 40, position_text)
        
        # Highlight top 5 positions in red
        if position <= 5:
            p.setFillColor(colors.red)
            p.drawString(box_x + 110, summary_y - 40, f"({position}{['st', 'nd', 'rd', 'th', 'th'][position-1]} POSITION)")
            p.setFillColor(colors.black)
        
        # Highlight FAILED if grade is F
        if student['grade'] == 'F':
            p.setFillColor(colors.red)
            p.drawString(box_x + 110, summary_y - 10, "FAILED")
            p.setFillColor(colors.black)

        # -------------------- SIGNATURES --------------------
        p.line(60, 100, 160, 100)
        p.line(230, 100, 330, 100)
        p.line(400, 100, 500, 100)

        p.setFont("Helvetica-Bold", 9)
        p.drawString(70, 85, "CLASS TEACHER")
        p.drawString(251, 85, "PRINCIPAL")
        p.drawString(425, 85, "PARENTS")

        # -------------------- ISSUED ON DATE AND TIME --------------------
        current_datetime = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        p.setFont("Helvetica", 8)
        p.setFillColor(colors.black)
        p.drawCentredString(width / 2, 30, f"Issued on: {current_datetime}")
        
        # End the page
        p.showPage()

    # Add the combined sheet if requested
    if include_combined:
        generate_combined_sheet(p, selected_students)
    
    p.save()
    buffer.seek(0)
    return buffer

# --- Function for Combined Result Sheet with Enhanced Design ---
def generate_combined_sheet(p, students):
    # Use landscape orientation for combined sheet
    width, height = landscape(A4)
    p.setPageSize((width, height))
    
    # Header section with Al Ghazali style
    p.setFont("Helvetica-Bold", 18)
    p.setFillColor(colors.HexColor("#0076BE"))
    p.drawCentredString(width / 2, height - 30, "Al Ghazali High School")

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.black)
    p.drawCentredString(width / 2, height - 48, "36/B, Landhi, Karachi, Near Daru-l-uloom Karachi")

    p.setFont("Helvetica-Bold", 14)
    p.setFillColor(colors.green)
    p.drawCentredString(width / 2, height - 70, f"Combined Marksheet For {datetime.now().year}")
    
    try:
        # Left logo
        left_logo_path = "Al Ghazali Logo.jpg"
        p.drawImage(
            ImageReader(left_logo_path),
            40,  # x-position
            height - 65,  # y-position
            width=50,
            height=50,
            preserveAspectRatio=True,
            mask='auto'
        )

        # Right logo
        right_logo_path = "Al Ghazali Logo1.jpg"
        p.drawImage(
            ImageReader(right_logo_path),
            width - 90,  # x-position
            height - 65,  # y-position
            width=50,
            height=50,
            preserveAspectRatio=True,
            mask='auto'
        )
    except:
        # If logo files don't exist, create placeholders
        p.setStrokeColor(colors.gray)
        p.ellipse(40, height - 65, 90, height - 15, stroke=1, fill=0)
        p.ellipse(width - 90, height - 65, width - 40, height - 15, stroke=1, fill=0)
    
    # Calculate table dimensions
    num_subjects = len(st.session_state.subjects)
    start_y = height - 90
    start_x = 20
    
    # Calculate column widths
    roll_width = 60  # Roll No column
    name_width = 110  # Name column
    class_width = 60  # Class column
    
    # Calculate subject width based on available space
    if num_subjects > 0:
        subj_width = min(40, (width - 40 - roll_width - name_width - class_width - 160) / num_subjects)
    else:
        subj_width = 40  # Default width if no subjects
    
    # Additional columns for total, obtained, etc.
    detail_width = 40
    
    # Draw table outline
    p.setStrokeColor(colors.black)
    p.setLineWidth(0.5)
    total_height = (len(students) + 1) * 25  # Height for all rows including header
    p.rect(start_x, start_y - total_height, width - 40, total_height, fill=0, stroke=1)
    
    # Draw header row with yellow background (Al Ghazali style)
    p.setFillColor(colors.yellow)
    p.rect(start_x, start_y - 25, width - 40, 25, fill=1, stroke=0)
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 8)
    
    # Draw column headers
    current_x = start_x
    
    # Roll No
    p.drawString(current_x + 5, start_y - 15, "Roll No")
    current_x += roll_width
    p.line(current_x, start_y, current_x, start_y - total_height)
    
    # Student Name
    p.drawString(current_x + 5, start_y - 15, "Student's Name")
    current_x += name_width
    p.line(current_x, start_y, current_x, start_y - total_height)
    
    # Class
    p.drawString(current_x + 5, start_y - 15, "Class")
    current_x += class_width
    p.line(current_x, start_y, current_x, start_y - total_height)
    
    # Subject columns - display in UPPERCASE
    for subject in st.session_state.subjects:
        # Abbreviate subject name if too long and convert to uppercase
        subject = subject.upper()
        display_name = subject if len(subject) <= 6 else subject[:5] + "."
        p.drawString(current_x + 2, start_y - 15, display_name)
        current_x += subj_width
        p.line(current_x, start_y, current_x, start_y - total_height)
    
    # Additional columns
    p.drawString(current_x + 5, start_y - 15, "Total")
    current_x += detail_width
    p.line(current_x, start_y, current_x, start_y - total_height)
    
    p.drawString(current_x + 5, start_y - 15, "Obt.")
    current_x += detail_width
    p.line(current_x, start_y, current_x, start_y - total_height)
    
    p.drawString(current_x + 2, start_y - 15, "Percent")
    current_x += detail_width
    p.line(current_x, start_y, current_x, start_y - total_height)
    
    p.drawString(current_x + 5, start_y - 15, "Grade")
    current_x += detail_width
    p.line(current_x, start_y, current_x, start_y - total_height)
    
    # Horizontal line under header
    p.line(start_x, start_y - 25, start_x + width - 40, start_y - 25)
    
    # Draw student data rows
    p.setFont("Helvetica", 7)
    
    for i, student in enumerate(students):
        current_y = start_y - ((i + 1) * 25) - 25
        current_x = start_x
        
        # No alternating row colors as per enhancement requirement 13
        
        # Calculate subject-wise results
        subject_results = []
        for mark in student['marks']:
            percentage, grade, _ = calculate_subject_result(mark, st.session_state.total_marks_per_subject)
            subject_results.append({
                'percentage': percentage,
                'grade': grade
            })
        
        # Roll No
        p.drawString(current_x + 5, current_y + 10, student['roll_no'])
        current_x += roll_width
        
        # Name - handle long names with abbreviation if needed
        name_display = student['name']
        if len(name_display) > 20:
            name_display = name_display[:18] + ".."
        p.drawString(current_x + 5, current_y + 10, name_display)
        current_x += name_width
        
        # Class
        p.drawString(current_x + 5, current_y + 10, student.get('class_name', 'N/A'))
        current_x += class_width
        
        # Subject marks with their individual grades
        for idx, mark in enumerate(student['marks']):
            # Write the mark
            p.drawString(current_x + 3, current_y + 15, str(mark))
            
            # Write the subject grade below the mark
            subject_grade = subject_results[idx]['grade']
            
            # Color code the grade
            if subject_grade == 'A+' or subject_grade == 'A':
                p.setFillColorRGB(0, 0.6, 0)
            elif subject_grade == 'F':
                p.setFillColorRGB(0.8, 0, 0)
            else:
                p.setFillColorRGB(0.2, 0.2, 0.7)
                
            p.drawString(current_x + 3, current_y + 5, subject_grade)
            p.setFillColor(colors.black)  # Reset color
            
            current_x += subj_width
        
        # Total possible marks
        total_possible = len(student['marks']) * st.session_state.total_marks_per_subject
        p.drawString(current_x + 5, current_y + 10, str(total_possible))
        current_x += detail_width
        
        # Obtained marks
        p.drawString(current_x + 5, current_y + 10, str(student['total']))
        current_x += detail_width
        
        # Percentage
        p.drawString(current_x + 3, current_y + 10, f"{student['percentage']:.1f}%")
        current_x += detail_width
        
        # Grade
        if student['grade'] == 'A+' or student['grade'] == 'A':
            p.setFillColorRGB(0, 0.6, 0)
        elif student['grade'] == 'F':
            p.setFillColorRGB(0.8, 0, 0)
        else:
            p.setFillColorRGB(0.2, 0.2, 0.7)
            
        p.drawString(current_x + 5, current_y + 10, student['grade'])
        p.setFillColor(colors.black)
        
        # Draw horizontal line after each row
        p.line(start_x, current_y, start_x + width - 40, current_y)
    
    # Signature section
    p.setFont("Helvetica-Bold", 9)
    p.line(80, 100, 180, 100)
    p.line(width/2 - 50, 100, width/2 + 50, 100)
    p.line(width - 180, 100, width - 80, 100)

    p.drawString(100, 85, "CLASS TEACHER")
    p.drawString(width/2 - 20, 85, "PRINCIPAL")
    p.drawString(width - 150, 85, "CONTROLLER")
    
    # Issued on date and time
    current_datetime = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    p.setFont("Helvetica", 8)
    p.drawCentredString(width / 2, 30, f"Issued on: {current_datetime}")
    
    p.showPage()

# --- Export to Excel ---
def export_to_excel():
    if st.session_state.students_data:
        df_data = []
        
        for student in st.session_state.students_data:
            student_row = {
                'Roll No': student['roll_no'],
                'Name': student['name'],
                'Father Name': student.get('father_name', ''),
                'Class': student.get('class_name', ''),
                'Total': student['total'],
                'Percentage': student['percentage'],
                'Grade': student['grade']
            }
            
            # Add subject marks
            for i, subject in enumerate(st.session_state.subjects):
                if i < len(student['marks']):
                    student_row[subject] = student['marks'][i]
                else:
                    student_row[subject] = 0
                    
            df_data.append(student_row)
            
        df = pd.DataFrame(df_data)
        
        # Convert to Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        output.seek(0)
        return output
    return None

# --- Import from Excel ---
def import_from_excel(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        
        # Clear existing data if any
        st.session_state.students_data = []
        
        # Extract subjects - all columns except standard ones
        standard_cols = ['Roll No', 'Name', 'Father Name', 'Class', 'Total', 'Percentage', 'Grade']
        subjects = [col for col in df.columns if col not in standard_cols]
        
        # Update session state subjects if they differ
        if sorted(subjects) != sorted(st.session_state.subjects):
            st.session_state.subjects = subjects
        
        # Process each row and add to students_data
        for _, row in df.iterrows():
            marks = [row[subject] for subject in subjects]
            
            # Calculate results in case they changed
            total, percentage, grade = calculate_result(marks, st.session_state.total_marks_per_subject)
            
            student = {
                'roll_no': str(row['Roll No']),
                'name': row['Name'],
                'father_name': row.get('Father Name', ''),
                'class_name': row.get('Class', 'N/A'),
                'marks': marks,
                'total': total,
                'percentage': percentage,
                'grade': grade
            }
            
            st.session_state.students_data.append(student)
        
        save_data()
        return True
    except Exception as e:
        st.error(f"Error importing data: {e}")
        return False

# --- Function to Reset Input Fields ---
def reset_input_fields():
    # Reset text inputs
    for key in st.session_state:
        if key.startswith('student_'):
            st.session_state[key] = ""
    
    # Reset mark inputs
    for subject in st.session_state.subjects:
        key = f"mark_{subject}"
        if key in st.session_state:
            st.session_state[key] = 0

# --- Streamlit App Layout ---
st.title("📚 AL-GHAZALI HIGH SCHOOL Marksheet System")

# Load existing data from JSON if available
if 'students_data' not in st.session_state:
    st.session_state.students_data = load_data()

# Initialize subjects if not present
if 'subjects' not in st.session_state:
    st.session_state.subjects = []
    
# Initialize total marks if not present
if 'total_marks_per_subject' not in st.session_state:
    st.session_state.total_marks_per_subject = 100

# Initialize timestamp
if 'timestamp' not in st.session_state:
    st.session_state.timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

# Sidebar menu
menu = st.sidebar.selectbox("📋 Menu", ["Setup Subjects", "Add Marksheet", "View All Marksheets", "Search Marksheet", "Download Marksheets"])

# --- Setup Subjects Once ---
if menu == "Setup Subjects":
    st.subheader("🔧 Setup Subjects and Total Marks")
    
    # Add class dropdown as requested
    class_options = ["Nursery", "KG"] + [f"Level-{i}" for i in range(1, 7)] + ["SSC-1", "SSC-2"]
    class_name = st.selectbox("Select Class", class_options, key="student_class")

    # Save selected class in session state (optional if needed elsewhere)
    if 'student_class_name' not in st.session_state:
        st.session_state['student_class_name'] = class_name
    else:
        st.session_state['student_class_name'] = class_name
    
    subject_count = st.number_input("How many subjects?", min_value=1, step=1)

    temp_subjects = []
    for i in range(int(subject_count)):
        subject_name = st.text_input(f"Subject {i+1} Name", key=f"sub_{i}")
        temp_subjects.append(subject_name)

    total_marks_input = st.number_input("Total Marks per Subject", min_value=1, step=1, value=100)

    if st.button("Save Setup"):
        if all(temp_subjects):
            st.session_state.subjects = temp_subjects
            st.session_state.total_marks_per_subject = total_marks_input
            st.success("✅ Subjects and Total Marks Saved!")
        else:
            st.error("Please enter all subject names.")

# --- Add Marksheet ---
elif menu == "Add Marksheet":
    st.subheader("➕ Add New Student Marksheet")
    
    # Check if subjects are set up
    if not st.session_state.subjects:
        st.warning("Please set up subjects first from the Setup Subjects menu!")
        st.stop()

    # Student info inputs
    student_name = st.text_input("Student Name", key="student_name")
    father_name = st.text_input("Father's Name", key="student_father_name")
    roll_no = st.text_input("Roll Number", key="student_roll")

    # Subject marks input
    st.write("Enter marks for each subject:")
    marks = []
    for subject in st.session_state.subjects:
        mark_input = st.text_input(f"{subject}", key=f"mark_{subject}")
        marks.append(mark_input)

    if st.button("Add Marksheet"):
    # Validation
        if not student_name:
            st.error("Please enter student name!")
        elif not all(marks):
            st.error("Please enter marks for all subjects!")
        else:
            try:
                float_marks = [float(mark) for mark in marks]

                for mark in float_marks:
                    if mark < 0 or mark > st.session_state.total_marks_per_subject:
                        st.error(f"Marks should be between 0 and {st.session_state.total_marks_per_subject}")
                        break
                else:
                    # Calculate result
                    total, percentage, grade = calculate_result(float_marks, st.session_state.total_marks_per_subject)

                    # Create student record
                    student = {
                        'roll_no': roll_no,
                        'name': student_name,
                        'father_name': father_name,
                        'class_name': st.session_state['student_class_name'],
                        'marks': float_marks,
                        'total': total,
                        'percentage': percentage,
                        'grade': grade,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    # Save and show success
                    st.session_state.students_data.append(student)
                    save_data()
                    st.success("✅ Marksheet Added Successfully!")

                    # Reset only relevant fields
                    keys_to_keep = ['students_data', 'subjects', 'total_marks_per_subject', 'student_class_name']
                    keys_to_delete = [key for key in st.session_state.keys() if key not in keys_to_keep]

                    for key in keys_to_delete:
                        del st.session_state[key]

                    # Try rerun (if available)
                    try:
                        st.experimental_rerun()
                    except AttributeError:
                        st.warning("Form reset. You can manually update the form if needed.")

            except ValueError:
                st.error("Please enter valid numeric marks!")



# --- View All Marksheets ---
elif menu == "View All Marksheets":
    st.subheader("👁️ View All Marksheets")
    
    if not st.session_state.students_data:
        st.info("No marksheets found. Please add marksheets first.")
    else:
        # Import/Export buttons (Enhancement #9)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Export as JSON"):
                # Prepare JSON for download
                json_str = json.dumps(st.session_state.students_data, indent=4)
                b64 = base64.b64encode(json_str.encode()).decode()
                href = f'<a href="data:file/json;base64,{b64}" download="students_data.json">Download JSON</a>'
                st.markdown(href, unsafe_allow_html=True)
        
        with col2:
            if st.button("Export as Excel"):
                excel_data = export_to_excel()
                if excel_data:
                    b64 = base64.b64encode(excel_data.getvalue()).decode()
                    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="students_data.xlsx">Download Excel</a>'
                    st.markdown(href, unsafe_allow_html=True)
        

        
        with col3:
            # Delete All Marksheets button (Enhancement #10)
            if st.button("Delete All Marksheets"):
                confirm_delete = st.checkbox("I understand this will delete all marksheets permanently")
                if confirm_delete:
                    st.session_state.students_data = []
                    save_data()
                    st.success("All marksheets deleted successfully!")
                    # Rerun to refresh the page
                    st.experimental_rerun()
        
        # Display all marksheets with Edit option (Enhancement #8)
        upload_file = st.file_uploader("Import Data", type=['json', 'xlsx'])
        if upload_file is not None:
            if upload_file.name.endswith('.json'):
                # Import JSON
                data = json.load(upload_file)
                st.session_state.students_data = data
                save_data()
                st.success("Data imported successfully!")
            elif upload_file.name.endswith('.xlsx'):
                # Import Excel
                if import_from_excel(upload_file):
                    st.success("Data imported successfully from Excel!")
                    
        for i, student in enumerate(st.session_state.students_data):
            with st.expander(f"{student['name']} - Roll No: {student['roll_no']} - Class: {student.get('class_name', 'N/A')}"):
                edit_col, view_col, delete_col = st.columns([1,1,1])
                
                with edit_col:
                    if st.button("Edit", key=f"edit_{i}"):
                        st.session_state.editing_student = i
                        # Set form values for editing
                        st.session_state.edit_name = student['name']
                        st.session_state.edit_father_name = student.get('father_name', '')
                        st.session_state.edit_roll_no = student['roll_no']
                        st.session_state.edit_class = student.get('class_name', 'Nursery')
                        
                        # Set mark values
                        for j, subject in enumerate(st.session_state.subjects):
                            if j < len(student['marks']):
                                st.session_state[f"edit_mark_{subject}"] = student['marks'][j]
                
                with view_col:
                    if st.button("View PDF", key=f"view_{i}"):
                        # Generate single marksheet
                        pdf = generate_individual_pdfs([student], include_combined=False)
                        
                        # Create download link
                        b64 = base64.b64encode(pdf.getvalue()).decode()
                        href = f'<a href="data:application/pdf;base64,{b64}" download="{student["name"]}_marksheet.pdf">Download PDF</a>'
                        st.markdown(href, unsafe_allow_html=True)
                
                with delete_col:
                    if st.button("Delete", key=f"delete_{i}"):
                        confirm = st.checkbox("Confirm delete", key=f"confirm_{i}")
                        if confirm:
                            st.session_state.students_data.pop(i)
                            save_data()
                            st.success("Marksheet deleted!")
                            st.experimental_rerun()
                
                # Display basic info
                st.write(f"**Name:** {student['name']}")
                st.write(f"**Father's Name:** {student.get('father_name', 'N/A')}")
                st.write(f"**Class:** {student.get('class_name', 'N/A')}")
                st.write(f"**Roll No:** {student['roll_no']}")
                st.write(f"**Total:** {student['total']} / {len(student['marks']) * st.session_state.total_marks_per_subject}")
                st.write(f"**Percentage:** {student['percentage']:.2f}%")
                st.write(f"**Grade:** {student['grade']}")
                
                # Display subject-wise marks
                subject_data = []
                for j, (subject, mark) in enumerate(zip(st.session_state.subjects, student['marks'])):
                    percentage, grade, remarks = calculate_subject_result(mark, st.session_state.total_marks_per_subject)
                    subject_data.append({
                        "Subject": subject.upper(),  # Enhancement #12: Subject names in uppercase
                        "Marks": mark,
                        "Percentage": f"{percentage:.2f}%",
                        "Grade": grade,
                        "Remarks": remarks
                    })
                
                # Show as table
                st.table(subject_data)
        
        # Edit Form (shown only when editing)
        if 'editing_student' in st.session_state:
            st.subheader("Edit Marksheet")
            
            edit_student = st.session_state.students_data[st.session_state.editing_student]
            
            # Edit form fields
            new_name = st.text_input("Student Name", value=st.session_state.edit_name, key="edit_name_input")
            new_father_name = st.text_input("Father's Name", value=st.session_state.edit_father_name, key="edit_father_name_input")
            
            # Class selection
            class_options = ["Nursery", "KG"] + [f"Level-{i}" for i in range(1, 7)] + ["SSC-1", "SSC-2"]
            new_class = st.selectbox("Select Class", class_options, index=class_options.index(st.session_state.edit_class) if st.session_state.edit_class in class_options else 0, key="edit_class_input")
            
            new_roll_no = st.text_input("Roll Number", value=st.session_state.edit_roll_no, key="edit_roll_no_input")
            
            # Subject marks
            new_marks = []
            for j, subject in enumerate(st.session_state.subjects):
                mark_value = 0
                if j < len(edit_student['marks']):
                    mark_value = edit_student['marks'][j]
                
                mark_key = f"edit_mark_{subject}"
                if mark_key not in st.session_state:
                    st.session_state[mark_key] = mark_value
                
                new_mark = st.number_input(f"{subject}", min_value=0.0, max_value=float(st.session_state.total_marks_per_subject), value=st.session_state[mark_key], key=f"edit_{mark_key}_input")
                new_marks.append(new_mark)
            
            update_col, cancel_col = st.columns(2)
            
            with update_col:
                if st.button("Update Marksheet"):
                    # Calculate new values
                    total, percentage, grade = calculate_result(new_marks, st.session_state.total_marks_per_subject)
                    
                    # Update student record
                    st.session_state.students_data[st.session_state.editing_student] = {
                        'roll_no': new_roll_no,
                        'name': new_name,
                        'father_name': new_father_name,
                        'class_name': new_class,
                        'marks': new_marks,
                        'total': total,
                        'percentage': percentage,
                        'grade': grade,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Save to JSON
                    save_data()
                    
                    # Clear editing state
                    if 'editing_student' in st.session_state:
                        del st.session_state.editing_student
                    
                    # Success message
                    st.success("✅ Marksheet Updated Successfully!")
                    st.experimental_rerun()
            
            with cancel_col:
                if st.button("Cancel Edit"):
                    # Clear editing state
                    if 'editing_student' in st.session_state:
                        del st.session_state.editing_student
                    st.experimental_rerun()

# --- Search Marksheet ---
elif menu == "Search Marksheet":
    st.subheader("🔍 Search Marksheet")
    
    search_options = ["Name", "Roll No", "Class"]
    search_by = st.selectbox("Search By", search_options)
    
    search_term = st.text_input("Enter Search Term")
    
    if st.button("Search") and search_term:
        found_students = []
        
        for student in st.session_state.students_data:
            if search_by == "Name" and search_term.lower() in student['name'].lower():
                found_students.append(student)
            elif search_by == "Roll No" and search_term.lower() in student['roll_no'].lower():
                found_students.append(student)
            elif search_by == "Class" and search_term.lower() in student.get('class_name', '').lower():
                found_students.append(student)
        
        if found_students:
            st.success(f"Found {len(found_students)} marksheet(s)")
            
            for i, student in enumerate(found_students):
                with st.expander(f"{student['name']} - Roll No: {student['roll_no']} - Class: {student.get('class_name', 'N/A')}"):
                    # Display basic info
                    st.write(f"**Name:** {student['name']}")
                    st.write(f"**Father's Name:** {student.get('father_name', 'N/A')}")
                    st.write(f"**Class:** {student.get('class_name', 'N/A')}")
                    st.write(f"**Roll No:** {student['roll_no']}")
                    st.write(f"**Total:** {student['total']} / {len(student['marks']) * st.session_state.total_marks_per_subject}")
                    st.write(f"**Percentage:** {student['percentage']:.2f}%")
                    st.write(f"**Grade:** {student['grade']}")
                    
                    # Display subject-wise marks
                    subject_data = []
                    for j, (subject, mark) in enumerate(zip(st.session_state.subjects, student['marks'])):
                        percentage, grade, remarks = calculate_subject_result(mark, st.session_state.total_marks_per_subject)
                        subject_data.append({
                            "Subject": subject.upper(),  # Enhancement #12: Subject names in uppercase
                            "Marks": mark,
                            "Percentage": f"{percentage:.2f}%",
                            "Grade": grade,
                            "Remarks": remarks
                        })
                    
                    # Show as table
                    st.table(subject_data)
                    
                    # View PDF button
                    if st.button("View PDF", key=f"view_search_{i}"):
                        # Generate single marksheet
                        pdf = generate_individual_pdfs([student], include_combined=False)
                        
                        # Create download link
                        b64 = base64.b64encode(pdf.getvalue()).decode()
                        href = f'<a href="data:application/pdf;base64,{b64}" download="{student["name"]}_marksheet.pdf">Download PDF</a>'
                        st.markdown(href, unsafe_allow_html=True)
        else:
            st.error(f"No marksheets found for {search_term}")

# --- Download Marksheets ---
elif menu == "Download Marksheets":
    st.subheader("📥 Download Marksheets")
    
    if not st.session_state.students_data:
        st.info("No marksheets found. Please add marksheets first.")
    else:
        # Filter options
        filter_options = ["All", "By Class", "By Roll No", "By Name"]
        filter_by = st.selectbox("Filter By", filter_options)
        
        selected_students = []
        
        if filter_by == "All":
            selected_students = st.session_state.students_data
        elif filter_by == "By Class":
            class_options = ["Nursery", "KG"] + [f"Level-{i}" for i in range(1, 7)] + ["SSC-1", "SSC-2"]
            selected_class = st.selectbox("Select Class", class_options)
            selected_students = [s for s in st.session_state.students_data if s.get('class_name') == selected_class]
        elif filter_by == "By Roll No":
            roll_input = st.text_input("Enter Roll Number")
            if roll_input:
                selected_students = [s for s in st.session_state.students_data if roll_input.lower() in s['roll_no'].lower()]
        elif filter_by == "By Name":
            name_input = st.text_input("Enter Student Name")
            if name_input:
                selected_students = [s for s in st.session_state.students_data if name_input.lower() in s['name'].lower()]
        
        # Show selected students
        if selected_students:
            st.write(f"Selected {len(selected_students)} marksheet(s)")
            
            # Show preview table
            preview_data = []
            for student in selected_students:
                preview_data.append({
                    "Name": student['name'],
                    "Roll No": student['roll_no'],
                    "Class": student.get('class_name', 'N/A'),
                    "Total": student['total'],
                    "Percentage": f"{student['percentage']:.2f}%",
                    "Grade": student['grade']
                })
            
            st.table(preview_data)
            
            # Download buttons with two options (Enhancement #11)
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Download With Combined Sheet"):
                    pdf = generate_individual_pdfs(selected_students, include_combined=True)
                    b64 = base64.b64encode(pdf.getvalue()).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="marksheets_with_combined.pdf">Download PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)
            
            with col2:
                if st.button("Download Without Combined Sheet"):
                    pdf = generate_individual_pdfs(selected_students, include_combined=False)
                    b64 = base64.b64encode(pdf.getvalue()).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="marksheets_individual.pdf">Download PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)
        else:
            st.info("No marksheets found with the selected filter.")

# Add CSS for smooth field navigation (Enhancement #1)
st.markdown("""
<style>
    /* Add custom CSS for better spacing and navigation */
    div.row-widget.stButton > button {
        width: 100%;
        margin-top: 10px;
    }
    
    div.row-widget.stTextInput > div > div > input {
        margin-bottom: 5px;
    }
    
    /* Highlight active input */
    div.row-widget.stTextInput > div > div > input:focus {
        border-color: #0076BE;
        box-shadow: 0 0 0 2px rgba(0, 118, 190, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- Add JS for field navigation (Enhancement #1 & #3) ---
js_code = """
<script>
document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && e.target.tagName.toLowerCase() === 'input') {
        e.preventDefault();
        const inputs = Array.from(document.querySelectorAll('input:not([type="hidden"])'));
        const currentIndex = inputs.indexOf(e.target);
        const nextInput = inputs[currentIndex + 1];
        
        if (nextInput) {
            nextInput.focus();
        }
    }
});
</script>
"""
st.markdown(js_code, unsafe_allow_html=True)
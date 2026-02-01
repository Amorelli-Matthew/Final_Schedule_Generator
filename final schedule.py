import requests
import sys #Only used for exitng the program
from bs4 import BeautifulSoup
import pypdf #Used for reading from a pdf file 
import re #Used for reg edit expressions
import csv

DAY_MAP = {
    "Monday": "M",
    "Tuesday": "T",
    "Wednesday": "W",
    "Thursday": "R",
    "Friday": "F"
}

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
DAY_LETTER = {
    "Monday": "M",
    "Tuesday": "T",
    "Wednesday": "W",
    "Thursday": "R",
    "Friday": "F"
}

def normalize_days(days_text):
    if not days_text:
        return "N/A"

    days_text = days_text.strip()

    # Case 1: Monday to Thursday
    if "to" in days_text:
        start, end = [d.strip() for d in days_text.split("to")]

        if start in DAY_ORDER and end in DAY_ORDER:
            start_idx = DAY_ORDER.index(start)
            end_idx = DAY_ORDER.index(end)

            letters = "".join(
                DAY_LETTER[day]
                for day in DAY_ORDER[start_idx:end_idx + 1]
            )

            # Compress common finals patterns
            if letters == "MTWRF":
                return "MWF"
            if letters == "MTWR":
                return "MW" 
            
            return letters

    # Case 2: Explicit days
    pattern = ""
    for day in DAY_ORDER:
        if day in days_text:
            pattern += DAY_LETTER[day]

    return pattern


def normalize_time(text):
    if not text:
        return text

    # Clean the text
    text = text.strip()

    # Convert time to the same format as website
    text = re.sub(
        r'^(\d{1,2})\s*([AaPp])\.?\s*[Mm]\.?$',
        lambda m: f"{m.group(1)}:00 {'a.m.' if m.group(2).lower() == 'a' else 'p.m.'}",
        text
    )

    text = re.sub(
        r'(\d{1,2}:\d{2})\s*([AaPp])\.?\s*[Mm]\.?',
        lambda m: f"{m.group(1)} {'a.m.' if m.group(2).lower() == 'a' else 'p.m.'}",
        text
    )

    return text

def fix_time_format(text):
    '''Fixes class time to match website format'''

    # Fix time format from 10:30AM to 10:30 a.m. 
    text = re.sub(r'(\d+:\d+)\s*([AaPp])[Mm]', r'\1 \2.m.', text)
    # Make AM/PM lowercase a.m./p.m.
    text = text.replace('AM.m.', 'a.m.').replace('PM.m.', 'p.m.').replace('AM', 'a.m.').replace('PM', 'p.m.')
    
    #Ensure space between time and a.m./p.m.
    text = re.sub(r'(\d+:\d+)([ap]\.m\.)', r'\1 \2', text, flags=re.IGNORECASE)
    return text


def extract_course_schedule(pdf_path):
    '''Extracts course schedule from the mynevada PDF file'''
    # Read in raw text
    text = ""
    with open(pdf_path, "rb") as file:
        reader = pypdf.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""

    # Formats merged digits, AM/PM, and Room Codes
    text = re.sub(r'(\d+)(AM|PM)', r'\1 \2', text)
    text = re.sub(r'(AM|PM)([A-Z]{2,})', r'\1 \2', text)
    
    # Add space before ADEnrolled to separate it from course names
    text = re.sub(r'([a-zA-Z])(ADEnrolled)', r'\1 \2', text, flags=re.IGNORECASE)
    text = re.sub(r'([a-zA-Z])(Enrolled)', r'\1 \2', text, flags=re.IGNORECASE)

    # Split into sections by Course Code
    course_sections = re.split(r'(?=[A-Z]{2,}\s+\d{3}\s+)', text)
    
    # Create a new final schedule list
    final_schedule = []

    # Goes through each class
    for section in course_sections:
        if not section.strip():
            continue

        # Extract the full course name and number
        name_match = re.search(r'^([A-Z]{2,}\s+\d{3}[^"]+?)(?=\s*(?:Enrolled|ADEnrolled|Days:|Times:|Class #|$))', section, re.DOTALL | re.IGNORECASE)
        
        if name_match:
            full_course_info = name_match.group(1).strip().replace('\n', ' ')
            
            # Extract the course name without abbreviation and number
            course_name_match = re.match(r'^[A-Z]{2,}\s+\d{3}\s+(.+)$', full_course_info)
            
            if course_name_match:
                course_name_only = course_name_match.group(1).strip()
            else:
                #Try to extract after the course number
                course_name_only = re.sub(r'^[A-Z]{2,}\s+\d{3}\s*', '', full_course_info).strip()
            
            # Check if this is an audit course, if so then skips it
            if "ADEnrolled" in section or "Audit" in section:
                continue
                
            # Check if enrolled
            if "Enrolled" in section:
                # Extract Days
                days_match = re.search(r'Days:\s*([A-Za-z\s\-to]+)', section, re.IGNORECASE)
                days = days_match.group(1).strip() if days_match else "N/A"
                
                # Extract only the Start Time
                time_match = re.search(r'Times:\s*(\d{1,2}:\d{2}\s*[APM]{2}|\d{1,2}\s*[APM]{2})', section, re.IGNORECASE)
                start_time = time_match.group(1) if time_match else "N/A"
                
                final_schedule.append({
                    "Course": course_name_only,
                    "Days": normalize_days(days),
                    "Start_Time": normalize_time(start_time)
                })
   
    return final_schedule
def extract_tables_from_webpage(soup):
    tables_data = []
    for table_tag in soup.find_all("table", class_="footable"):
        caption = table_tag.find("caption")
        
        # Extract day from caption
        if caption:
            day_text = caption.get_text(strip=True)
            # Get just the day name (e.g., "Thursday" from "Thursday, First day of finals")
            day = day_text.split(',')[0].strip()
        else:
            day = "Unknown"

        rows = []
        
        for tr in table_tag.select("tbody tr"):
            cells = [td.get_text(strip=True).replace("\xa0", " ").strip() for td in tr.find_all("td")]
            
            if len(cells) >= 3:
                # Normalize the class time
                class_time = normalize_time(cells[0])
                class_days_text = cells[1]
                final_time = cells[2]
                
                # Extract day pattern from parentheses, e.g., "(MW)" from "Monday/Wednesday/Friday (MWF)"
                day_pattern_match = re.search(r'\(([A-Z]+)\)', class_days_text)
                if day_pattern_match:
                    day_pattern = day_pattern_match.group(1)
                else:
                    # Fallback: Try to determine pattern from text
                    if 'Tuesday/Thursday' in class_days_text or 'TR' in class_days_text:
                        day_pattern = 'TR'
                    elif 'Monday/Wednesday/Friday' in class_days_text or 'MWF' in class_days_text:
                        day_pattern = 'MWF'
                    elif 'Monday/Wednesday' in class_days_text or 'MW' in class_days_text:
                        day_pattern = 'MW'
                    elif 'Monday' in class_days_text:
                        day_pattern = 'M'
                    elif 'Tuesday' in class_days_text:
                        day_pattern = 'T'
                    elif 'Wednesday' in class_days_text:
                        day_pattern = 'W'
                    elif 'Thursday' in class_days_text:
                        day_pattern = 'R'
                    elif 'Friday' in class_days_text:
                        day_pattern = 'F'
                    else:
                        day_pattern = "Unknown"
                
                rows.append({
                    "class_time": class_time,
                    "day_pattern": day_pattern,
                    "final_time": final_time
                })

        tables_data.append({
            "day": day,
            "rows": rows
        })
    return tables_data

def find_final_exam_time(student_class, tables_data):

    student_days = student_class['Days']
    student_time = student_class['Start_Time']
    
    for table in tables_data:
        day = table["day"]
        for row in table["rows"]:
            # Check if day patterns match
            if row["day_pattern"] == student_days:
                # Check if times match
                website_time = row["class_time"]
                
                # Extract just the hour for comparison
                student_hour_match = re.search(r'(\d{1,2}):', student_time)
                website_hour_match = re.search(r'(\d{1,2}):', website_time)
                
                if student_hour_match and website_hour_match:
                    student_hour = int(student_hour_match.group(1))
                    website_hour = int(website_hour_match.group(1))
                    
                    # Adjust for morning or night
                    if 'p.m.' in student_time and student_hour < 12:
                        student_hour += 12
                    if 'p.m.' in website_time and website_hour < 12:
                        website_hour += 12
                    
                    # Check if hours match 
                    if abs(student_hour - website_hour) <= 1:
                        return {
                            "Course": student_class['Course'],
                            "Final_Day": day,
                            "Final_Time": row["final_time"]
                        }
    
    # If no match found
    return {
        "Course": student_class['Course'],
        "Final_Day": "Not Found",
        "Final_Time": "Not Found"
    }

def write_to_csv(finals_schedule, filename="finals_schedule.csv"):
    '''Writes the finals schedule to a CSV file'''

    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['Course', 'Final_Day', 'Final_Time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for exam in finals_schedule:
            writer.writerow(exam)
    
    print(f"Finals schedule saved to '{filename}'")

def main(args):
    print("UNR Finals Schedule Generator")
    print("==============================")
    url = "https://www.unr.edu/admissions/records/academic-calendar/finals-schedule"

    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        soup = BeautifulSoup(r.text, 'html.parser')
    else:
      print("Error fetching finals schedule")
      return
    


    # Parse tables from webpage
    tables_data = extract_tables_from_webpage(soup)

    # Get PDF file path from args if no file then exit
    if len(args) > 0:
        file_path = args[0]
    else:
        print("Error no file")
        sys.exit(1)
    
    # Extract course schedule
    schedule = extract_course_schedule(file_path)
    
   

    # Find final exam for each course
    finals_schedule = []
    for student_class in schedule:
        final_info = find_final_exam_time(student_class, tables_data)
        finals_schedule.append(final_info)
       
    # Write to CSV
    write_to_csv(finals_schedule)
    
 
if __name__ == "__main__":
    #Grab user input as an argument
    main(sys.argv[1:])
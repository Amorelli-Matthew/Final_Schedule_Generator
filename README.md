# UNR Finals Schedule Generator

## Description
A Python-based web scraper that extracts a UNR student's course schedule from a PDF file and matches it against the University of Nevada, Reno's official finals schedule webpage. The program programmatically generates a personalized finals schedule for the semester and saves the results to a CSV file.

**Key Features:**
- Extracts course information (like name, meeting days, start times) from PDF schedule files
- Scrapes the official UNR finals schedule from their website
- Matches student courses with corresponding final exam times using intelligent pattern matching
- Outputs a clean, organized CSV file with final exam details
- Handles edge cases like audit courses and various time formats

## Prerequisites

### Python Version
- Python 3.14 or higher

### Required Python Libraries
- Built in: csv re

#### Install the following packages using pip:
- pip install requests beautifulsoup4 pypdf

### To Run
```
python3 ./final_schedule.py myclasses.pdf
```
#### Note:
myclasses can be any other MyNevada class Schedule PDF file



# Example Console Output
```
UNR Finals Schedule Generator
==============================
Finals Schedule saved to 'finals_schedule.csv'
```

## Example finals_schedule.csv
```
Course,Final_Day,Final_Time
Prog Lang Conc Implmnt,Tuesday,10:15 a.m.-12:15 p.m.
Automata & Formal Lang,Thursday,10:15 a.m.-12:15 p.m.
Database Mgmt Systems,Monday,3-5 p.m.
Circuits I,Friday,10:15 a.m.-12:15 p.m.
```
## License Notice
Licensed as GPLV3 See `LICENSE` for details Exception.

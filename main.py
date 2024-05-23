import pandas as pd
import os
import re
import pytesseract
from pdf2image import convert_from_path
import fitz
import enchant

#instantiates enchant module
d = enchant.Dict('en_US') 

def write_text(directory, txt_name):
    """
    Converts an un-scanned (ie text is not able to be highlighted) pdfs into a text file using pytesseract ;;main, svl

    Args:
    directory: directory that holds all the unscanned pdfs
    txt_name: txt file that will hold all converted pdfs-to-strings
    """
    f = open(txt_name, 'w')
    count = 0

    #checks if file
    for filename in os.listdir(directory):
        if not filename == '.DS_Store':
            filepath = os.path.join(directory, filename)

            #check if file
            if os.path.isfile(filepath):
                pages = convert_from_path(filepath, 300)
                text = ''

                for page in pages:
                    #use pytesseract to perform OCR on the image
                    text += pytesseract.image_to_string(page)

                #clean text
                no_space = '|()[]{}_"=~—«©°”€’$®*+¢“%><;'
                for char in no_space:
                    text = text.replace(char, '')
                text = text.replace('\xa0', ' ')
                text = text.replace('\n', ' ')
                text = text.replace('--', '-')
                text = text.replace('  ', ' ')
                text = text.lower()

                f.write(str(filename) + ' ' + text + '\n')
                count += 1
                print(count)
    f.close()

#main
def create_datum(text):
    """
    Iterated method to get date and time of crash, number of people injured or killed (no difference in research purposes),
    location of crash (street one and street two, if exist), and whether the accident occurred at a crosswalk and/or
    parking lot

    Args:
    text: string representation of accident report

    Returns:
    dictionary mapping label to information
    """
    curr_data = {}

    pdf = text.find('pdf')
    curr_data['Filepath'] = text[:pdf + 3]

    #date of crash, time of crash, number of people injured
    days = [' sun ', ' mon ', ' tue ', 'wed ', 'thu ', ' fri ', ' sat ']
    day_index = 0
    for day in days:
        if text.find(day) != -1:
            day_index = text.find(day)
            break
    time_index = text[day_index:].find(':')

    date_string = text[day_index - 8: day_index].replace(' ', '')
    if not date_string.isnumeric():
        curr_data['Date_of_Crash'] = None
    else:
        curr_data['Date_of_Crash'] = text[day_index - 8: day_index].replace(' ', '/')

    time_string = text[day_index + time_index - 2: day_index + time_index + 3].replace(':', "")
    if not time_string.isnumeric():
        curr_data['Time_of_Crash(2400_hours)'] = None
    else:
        curr_data['Time_of_Crash(2400_hours)'] = text[day_index + time_index - 2: day_index + time_index + 3]

    str_dig = '123456789'
    injury_death = text[day_index + time_index + 7:].find('.')
    if injury_death > 15:
        curr_data['Was_Injured'] = None
    for char in text[day_index + time_index + 8: day_index + time_index + injury_death + 7]:
        if char in str_dig:
            curr_data['Was_Injured'] = char
            break
        else:
            curr_data['Was_Injured'] = 0

    #first street name
    occured_on = text.find('occured on:')  #misspelled occurred
    substr = text[occured_on:-1]
    idx = 0
    for char in substr:
        if char == '-':
            idx = substr.index(char)
            break
    substr = text[occured_on + len('occured on:'): occured_on + idx]
    substr = substr.replace('-', '')
    if len(substr) > 50:
        curr_data['Street_One'] = None
    else:
        curr_data['Street_One'] = substr.strip()

    #second street name
    feet = text.find('feet')
    station = text.find('station/precinct')
    substr = [group for group in text[feet + len('feet'):station].split(' ') if group.isalpha()]
    lst = []
    for group in substr:
        if len(group) > 3 and 'speed' not in d.suggest(group) and 'limit' not in d.suggest(group):
            lst.append(group)
        elif len(group) == 3 and d.check(group):
            lst.append(group)
    substr = ' '.join([i for i in lst])
    if len(substr) > 50 or ' ' not in substr:
        curr_data['Street_Two'] = None
    else:
        curr_data['Street_Two'] = substr.strip()

    #accident at crosswalk or parking lot
    curr_data['At_Crosswalk'] = 'crosswalk' in text
    curr_data['At_ParkingLot'] = 'parking lot' in text

    return curr_data


#svl
def create_datum_svl(text):
    """
    Iterated method to get date and time of crash, number of people injured or killed (no difference in research purposes),
    location of crash (street one and street two, if exist), and whether the accident occurred at a crosswalk and/or
    parking lot. Due to the differences in abbreviations used based on town, methods were slightly modified to retrieve the 
    same information.

    Args:
    text: string representation of accident report
    """
    curr_data = {}

    pdf = text.find('pdf')
    curr_data['Filepath'] = text[:pdf + 3]

    #date of crash, time of crash, number of people injured
    days = [' sunday ', ' monday ', ' tuesday ', ' wednesday ', ' thursday ', ' friday ', ' saturday ']
    day_index = 0
    new_day = 0
    for day in days:
        if text.find(day) != -1:
            day_index = text.find(day)
            new_day = day_index + len(day)
            break
    date_string = text[day_index - 10: day_index]
    curr_data['Date_of_Crash'] = date_string

    time_string = text[new_day: new_day + 4]
    curr_data['Time_of_Crash(2400_hours)'] = time_string[:2] + ":" + time_string[2:]

    injury_death = text[day_index: day_index + 20].split(' ')
    if day_index == 0:
        curr_data['Was_Injured'] = None
    else:
        injury_death_count = 0
        for element in injury_death:
            if len(element) == 1:
                injury_death_count += int(element)
        curr_data['Was_Injured'] = int(injury_death_count)

        # first street name
        occurred_on = text.find('occurred on:')  
        substr = text[occurred_on:-1]
        idx = substr.find('2.')
        substr = text[occurred_on + len('occurred on: '): occurred_on + idx]
        if idx == 0 or len(substr) > 50:
            curr_data['Street_One'] = None
        else:
            curr_data['Street_One'] = substr

    #second street name
    station = text.find('station/precinct')
    crossroad = text.find('cross road name/route')
    substr = [group for group in text[feet + len('feet'):crossroad].split(' ') if group.isalpha()]
    lst = []
    for group in substr:
        if len(group) > 3 and 'speed' not in d.suggest(group) and 'limit' not in d.suggest(group):
            lst.append(group)
        elif len(group) == 3 and d.check(group):
            lst.append(group)
    substr = ' '.join([i for i in lst])
    if len(substr) > 50 or ' ' not in substr:
        curr_data['Street_Two'] = None
    else:
        curr_data['Street_Two'] = substr.strip()

    #accident at crosswalk or parking lot
    curr_data['At_Crosswalk'] = 'crosswalk' in text
    curr_data['At_ParkingLot'] = 'parking lot' in text

    return curr_data


#main, svl
def create_data(directory, txt_name):
    """
    Iterates through all the string representations of accident reports to create the data

    Args:
    directory: directory that holds town's accident reports
    txt_name: txt file that holds string representations of each accident report

    Returns:
    list of all data
    """
    if not os.path.exists(txt_name):
        write_text(directory, txt_name)

    file = open(txt_name, 'r')
    lines = file.readlines()

    data = []
    count = 0

    for line in lines:
        data.append(create_datum(line))
        count += 1

    return data

#main, svl
def create_csv(directory, txt_name, csv_name):
    """
    First creates pandas DataFrame from the data, which is then turned into a csv

    Args:
    directory: directory that holds all the pdf accident reports
    txt_name: txt file to write string representations of accident reports to
    csv_name: csv file to write pandas DataFrame to
    """
    data = create_data(directory, txt_name)
    df = pd.DataFrame(data)
    if not os.path.exists(csv_name):
        df.to_csv(csv_name, encoding='utf-8', index=False)

#pdf table
def write_clean_txt(txt_name, pdf_path):
    """
    Converts unscanned pdf, cleans text, and writes to a txt file

    Args:
    txt_name: txt file that text of each pdf gets written to
    pdf_path: 
    """
    images = convert_from_path(pdf_path)
    extracted_text = ''
    for image in images:
        extracted_text += pytesseract.image_to_string(image)

    text = extracted_text.replace('\n\n','\n')
    text = text.replace('Police Department\n', '')
    text = text.replace('\n', ' ')
    #new line for each subheading
    text = text.replace('Case', '\nCase')
    text = text.replace('Date', '\nDate')
    text = text.replace('Location', '\nLocation')
    text = text.replace('Incident / Call Type', '\nIncident / Call Type')
    text = text.replace('Officer of Record', '\nOfficer of Record')

    with open(txt_name, 'w') as f:
        f.write(text)
    f.close()

    #rewrites over to clean.txt necessary lines (ie only Date and Location)
    with open(txt_name, 'r') as f:
        with open('clean.txt', 'w') as c:
            while True:
                line = f.readline()
                if not line:
                    break
                elif line.startswith('Date') or line.startswith('Location'):
                    c.write(line)

#pdftable
def create_dataframe(txt_name, filepath):
    """
    Creates dataframe for date and location of accident

    Args:
    txt_name: txt file that holds each date, location, etc on separate lines
    
    Returns:
    array that holds dates and locations (same length)
    """
    if not os.path.exists(txt_name):
        write_clean_txt(txt_name, filepath)

    dates = []
    locations = []
    with open('clean.txt', 'r') as f:
        while True:
            line = f.readline()
            if not line:
                break
            elif line.startswith('Date'):
                line_date = line.split('  ')
                for date in line_date[1:-1]:
                    if 'N' in date:
                        date = date.replace('N','/1') #pytessaract sometimes misinterpreted /1 as N
                        dates.append(date)
            elif line.startswith('Location'):
                line_loc = line.split(' ')
                for loc in line_loc[1:-1]:
                    locations.append(loc)

    return dates, locations


#proj, folder of pdfs, strings txt, dataframe csvs
#main
def run(data_path):
    """
    Creates csvs from all the accident reports based on the folder (ie town) which they came from

    Args:
    data_path: folder that holds the folders that hold the pdf accident reports

    Note:
    town_name_here is uniquely an image of a pdf, not an accident report. It is a table of accident report ids, 
    dates, location, and type of accident (all of which are Motor Vehicle Crashes, Pedestrians Struck).
    """
    for filename in os.listdir(data_path):
        if not filename == '.DS_Store':
            filepath = os.path.join(data_path, filename)
            if filename == 'town_name_here':
                dates, location = create_dataframe(filename + '.txt', filepath) 
                df = pd.DataFrame({
                    'Dates': dates,
                    'Locations': location
                })
                csv = ''
                df.to_csv(csv, encoding='utf-8', index=False)
            else:
                create_csv(filepath, filename + '_strings.txt', filename + '.csv')

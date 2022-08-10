# library

import os
from termcolor import colored
import pwd # needed if the document is stored on computer instead of Google Drive
import tkinter as tk
from tkinter import filedialog
import pandas as pd
pd.set_option('display.max_columns', None) # keeps pandas from truncating columns
import numpy as np
import clipboard
pd.options.display.max_colwidth = 1000
import warnings
warnings.filterwarnings('ignore')
from tabulate import tabulate
from datetime import datetime
import pytz

run_list = []

# Cell feedback
def cell_feedback():
    print(" ")
    print("Cell ran at:")
    tz_east = pytz.timezone('US/Eastern') 
    datetime_eastern = datetime.now(tz_east)
    print("Eastern:", datetime_eastern.strftime("%H:%M:%S"))

    tz_central = pytz.timezone('US/Central') 
    datetime_central = datetime.now(tz_central)
    print("Central:", datetime_central.strftime("%H:%M:%S"))

    tz_pacific = pytz.timezone('US/Pacific')
    datetime_pacific = datetime.now(tz_pacific)
    print("Pacific:", datetime_pacific.strftime("%H:%M:%S"))


import subprocess
import platform

def raise_app(root: tk):
    root.attributes("-topmost", True)
    if platform.system() == 'Darwin':
        tmpl = 'tell application "System Events" to set frontmost of every process whose unix id is {} to true'
        script = tmpl.format(os.getpid())
        output = subprocess.check_call(['/usr/bin/osascript', '-e', script])
    root.after(0, lambda: root.attributes("-topmost", False))


def get_task_list_file_and_validate():
    # Cell Name: FILE

    '''
    This cell is used to access the template file that we want to work with.

    This code was built for MacOS, but I will eventually set it up for Windows also.
    It checks if you have Google Drive Desktop App installed, and if so will open a path to the IMPORTS
    folder when looking for the file, otherwise it will open the 'Downloads' folder in the Finder. 

    If you have Google Drive Destop installed, but prefer to save files to your computer, set the check_for_google_drive
    variable to False (True and False are case sensitive). 
    '''

    check_for_google_drive = True
    local_folder = "Downloads" #you can change this to start at a different folder. 

    root = tk.Tk()
    # os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
    # root.wm_attributes('-topmost', 1)
    raise_app(root)
    root.withdraw()
    root.lift()

    file_path = '' #filedialog.askopenfilename()

    if check_for_google_drive:
        if 'Google Drive.app' in os.listdir("/Applications/"):
            root.file_path =  filedialog.askopenfilename(initialdir = "/Volumes/GoogleDrive/My Drive/IMPORTS",title = "SELECT the Task List File")
        else:
            root.file_path =  filedialog.askopenfilename(initialdir = "/Users/"+pwd.getpwuid(os.getuid()).pw_name+"/{local_folder}",title = "SELECT the CSV file from Jira")
    else:
        root.file_path =  filedialog.askopenfilename(initialdir = "/Users/"+pwd.getpwuid(os.getuid()).pw_name+"/{local_folder}",title = "SELECT the CSV file from Jira")


    # print ('Source file: ' + root.file_path)

    '''
    This cell formats the import as a dictionary of DataFrames, and also collects other important bits of data.

    For this to work properly, the name of the folder that the file is in must lead with the team ID.
    '''

    team_id = root.file_path.split("/")[-2].split(" ")[0] 
    team_name = " ".join(root.file_path.split("/")[-2].split(" ")[1:])
    file_name = root.file_path.split("/")[-1]
    xl_file = pd.read_excel(root.file_path, sheet_name = None)
    xl_sheets = list(xl_file.keys())
    '''
    Sanity check to make sure that the information is collected correctly, and to give an overview of 
    what is present in the file. 
    '''

    print(f"Team ID:\t{team_id}")
    print(f"Team Name:\t{team_name}")
    print(f"File Name:\t{file_name}")
    for i in range(0, len(xl_sheets)):
        print(f"Sheet {i+1} (i={i}):   \t{xl_sheets[i]}")
    print(' ')

    # If the first column Header is 'Task List Name' then we need to capture this sheet. This will capture some sheets with no info, but later cleaning will remove that data. 

    task_sheet_names = [xl_sheets[i] for i in range(0, len(xl_sheets)) if xl_file[xl_sheets[i]][xl_file[xl_sheets[i]].columns[0]][0] == 'Task List Name*']

    archive_sheet_names = [xl_sheets[i] for i in range(0, len(xl_sheets)) if xl_file[xl_sheets[i]][xl_file[xl_sheets[i]].columns[0]][0] == 'Task List Name']
    if len(task_sheet_names) > 0:
        # print('Task list template sheets present.')
        
        pass
    elif len(archive_sheet_names) > 0:
        print(colored('Caution: ', 'yellow', attrs=['bold'])+"Noncurrent Task List Template.")
        task_sheet_names=archive_sheet_names
    else:
        print(colored("ERROR: No task list template sheets present.", 'red', attrs=['bold']))
        print(' ')

    # Fix the headers
    # The header for this data is all unknown (because Row one in the template isn't the header). Because row 2 (row 2 in the CSV mind you) is the header, we are setting that row as the header. 

    for i in task_sheet_names:
        xl_file[i].columns = xl_file[i].iloc[0]
        xl_file[i] = xl_file[i].drop(0, axis=0).reset_index(drop=True)
        xl_file[i].columns = xl_file[task_sheet_names[0]].columns.str.replace('*','').str.replace('Task or Notification\nT or N', 'Task or Notification?').str.replace('Assign task to role or assignee \(only for tasks\)', 'Assign to TC, Agent or assignee full name')
        if xl_file[i].columns[0] == 'Task List Name':
            # 
            pass
        else:
            print(colored(f'ERROR: {i} is not valid.', 'red', attrs=['bold']))
    print(' ')


    # Combine the sheets
    # We have a list of all the sheets that we will use (task_sheet_name) which we will use to combine all the sheets into a single DataFrame (df)
    print("SHEETS WITH TASKS AND COUNT OF TASKS/ROWS:")
    cols = np.append(xl_file[task_sheet_names[0]].columns, 'sheet_name')
    df = pd.DataFrame(columns = cols)

    sheet_len = 0
    for i in task_sheet_names:
        xl_file[i]['Task List Name'] = xl_file[i]['Task List Name'].replace({'':np.nan}).fillna(method = 'ffill')
        xl_file[i]['Task Name'] = xl_file[i]['Task Name'].replace({'':np.nan})
        xl_file[i] = xl_file[i][xl_file[i]['Task Name'].notna()]                    #Skip all rows with missing "task name"
        xl_file[i] = xl_file[i][xl_file[i]['Task Name'].str.contains("end of list")==False]
        xl_file[i]['sheet_name'] = i
        df = df.append(xl_file[i])
        file_len = len(xl_file[i][0:])
        print(colored(file_len,'cyan') + f" rows in {i}")
        sheet_len = sheet_len+file_len

    print(colored(sheet_len,'cyan')+ " rows in total.")
    print(' ')

    #Clean combined sheets
    # Some of this cleaning is redundant (but better safe than sorry). Removing the csv indicators for the end of list and instructions. Also, if the Task name is empty, then the row will be removed. 

    df = df[(df['Task List Name']!='Task List Name') & (df['Task List Name'].str.contains('end of list|Enter your task')==False) & (df['Task Name'].notna())]
    df = df.fillna('')
    df['Days'] = df['Days'].astype(str)
    df['Days'] = df['Days'].replace({'': '0'})
    df['Days'] = df['Days'].str.replace('--', '-')
    df['Days'] = df['Days'].fillna('0')
    if len(df[df['Days'].isna()])!=0:
        print(colored('Days contain NaN values. Use', 'red', attrs=['bold']) + ' df["Days"].value_counts(dropna=False) ' + colored('to check for strange characters in the coloumn.', 'red', attrs=['bold']))
    else:   
        print(colored('All empty Day values have been set to zero.', 'green', attrs=['bold']))

    df['List descr. remaining\ncharacters'] = 255 - df['List Description'].str.len()
    df['Task description remaining\ncharacters'] = 255 - df['Task Description'].str.len()
    df['Task name remaining\ncharacters'] = 255 - df['Task Name'].str.len()
    try:
        df = df.drop('← Limit', axis=1)
    except:
        pass

    list_desc_char_limit_exceeded_count = len(df[df['List descr. remaining\ncharacters']<0])
    if list_desc_char_limit_exceeded_count > 0:
        print(colored('WARNING: ','red', attrs=['bold']) + f"{list_desc_char_limit_exceeded_count} tasks have Task List Description that exceed the 255 character limit. Please review the customer submitted document.")
    else:
        pass
    task_desc_char_limit_exceeded_count = len(df[df['Task description remaining\ncharacters']<0])
    if task_desc_char_limit_exceeded_count>0:
        print(colored('WARNING: ','red', attrs=['bold']) + f"{task_desc_char_limit_exceeded_count} tasks have Task Description that exceed the 255 character limit. Please review the customer submitted document.")
    else:
        pass
    task_name_char_limit_exceeded_count = len(df[df['Task name remaining\ncharacters']<0])
    if task_name_char_limit_exceeded_count>0:
        print(colored('WARNING: ','red', attrs=['bold']) + f"{task_name_char_limit_exceeded_count} tasks have Task Name that exceed the 255 character limit. Please review the customer submitted document.")
    else:
        pass




    # This strips all the whitespace from around the strings in the DataFrame.
    for i in df.columns:
        '''
        Simple function says
            1. look at column
            2. if column is string, strip whitespace
            3. move to next column
            4. repeat until all columns checked
        '''
        if df[i].dtype == "O":    # strings in a DataFrame are called objects, and the dtype 'Object' of a column in a DataFrame is presented as 'O'  
            df[i] = df[i].str.strip() 
            df[i] = df[i].str.replace("UPDATE", "UP-DATE")
            df[i] = df[i].str.replace("update", "up-date")
            df[i] = df[i].str.replace("'", "")
            df[i] = df[i].str.replace('"', "")
            df[i] = df[i].str.replace('’', "") # special apostrophe
            df[i] = df[i].str.replace('–', "-") # Special hyphen
            df[i] = df[i].str.replace(r'”', "") # special quotations
            df[i] = df[i].str.replace(r'“', "") # special quotations
            df[i] = df[i].str.replace("\r", " - ")
            df[i] = df[i].str.replace("\n", "")
            df[i] = df[i].str.replace(chr(13), " - ")
            df[i] = df[i].str.replace(chr(10), "")
            df[i] = df[i].str.replace("➤", "")
            df[i] = df[i].str.replace('etc…', 'etc') # The elipses is a character that SISU doesn't acknowledge and drops
            df[i] = df[i].str.replace(r'<[^<>]*>', ' ', regex=True)
            df[i] = df[i].str.replace("&nbsp", " ")

            
            df[i] = df[i].str[0:254] # Truncates the value to 254 characters
            df[i] = df[i].str.strip() # Sometimes the truncation leaves blank space -- redundancy isn't a problem here



    df['List Description']  = df['List Description'].replace({'':np.nan}).fillna(method = 'ffill')

    df['List Description'] = df['List Description'].replace({'':np.nan}).fillna(method = 'ffill')
    df['List Description'] = df['List Description'].fillna('')
    # df['Buyer/Seller code'] = df['Buyer/Seller code'].replace({'':np.nan}).fillna(method = 'ffill')
    df['Applies to Buyer/Seller'] = df['Applies to Buyer/Seller'].replace({'':np.nan}).fillna(method = 'ffill')


    print(colored('All whitespace cleared from string values.', 'green', attrs=['bold']))
    print(' ')



    '''
    Alternate method for stripping the whitespace:

    df_obj = df.select_dtypes(['object'])
    df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())

    '''



    # def left_align(df):
    #     left_aligned_df = df.style.set_properties(**{'text-align': 'left'})
    #     left_aligned_df = left_aligned_df.set_table_styles(
    #         [dict(selector='th', props=[('text-align', 'left')])]
    #     )
    #     return left_aligned_df




    df = df.reset_index()
    # Validator For Task List Template

    # Columns
    version = 'current' # change if using older version
    if version == 'current':
        task_list_template_validation_cols = ['Task List Name', 'List Description',
        'List descr. remaining\ncharacters', 'Applies to Buyer/Seller',
        'Task Name', 'Task name remaining\ncharacters', 'Task Description',
        'Task description remaining\ncharacters',
        'Task Trigger date \n(Relative due date)', 'Trigger Date DB (Sisu)',
        'Assign to TC, Agent or assignee full name', 'Assign To T/A/Agent ID',
        'Days', 'Task or Notification?']

    else:
        task_list_template_validation_cols = ['Task List Name', 'List Description',
            'List descr. remaining\ncharacters', 'Applies to Buyer/Seller',
            'Buyer/Seller code', 'Task Name', 'Task name remaining\ncharacters',
            'Task Description', 'Task description remaining\ncharacters',
            'Task Trigger date \n(Relative due date)', 'Trigger Date DB (Sisu)',
            'Assign to TC, Agent or assignee full name', 'Assign To T/A/Agent ID',
            'Days', 'Task or Notification?']
    for i in task_list_template_validation_cols:
        if i in df.columns:
            pass
        else:
            print(colored(f"ERROR: Required column", 'red', attrs = ['bold']) + colored(f" {i} ", 'yellow', attrs=['bold']) + colored(f"not found in template.", 'red', attrs = ['bold']))
        

    df['Assign to TC, Agent or assignee full name'] = df['Assign to TC, Agent or assignee full name'].replace({'':np.nan})
    if len(df[(df['Assign to TC, Agent or assignee full name'].isna()) & (df['Task or Notification?'] == 'T')])>0:
        print(colored('THE FOLLOWING TASKS ARE MISSING ASSINEE:', 'red', attrs=['bold']) + f" TOTAL: {len(df[df['Assign to TC, Agent or assignee full name'].isna()])}")
        with pd.option_context("display.max_rows", 1000):  
            print(tabulate(df[df['Assign to TC, Agent or assignee full name'].isna()][['sheet_name','Task Name']]))

    df['Task or Notification?'] = df['Task or Notification?'].replace({'':np.nan})
    if len(df[(df['Task or Notification?'].isna()) | (df['Task or Notification?'].str.contains('T|N')==False)])>0:
        print(colored('THE FOLLOWING TASKS ARE MISSING, OR HAVE INCORRECT, "Task or Notification?" INFORMATION:', 'red', attrs=['bold']) + f" TOTAL: {len(df[(df['Task or Notification?'].isna()) | (df['Task or Notification?'].str.contains('T|N')==False)])}")
        with pd.option_context("display.max_rows", 1000):
            print(tabulate(df[(df['Task or Notification?'].isna()) | (df['Task or Notification?'].str.contains('T|N')==False)][['sheet_name','Task Name']]))

    # Corrects current Task List Template's Buyer/Seller code to match legacy version
    if version == 'current':
        df['Applies to Buyer/Seller'] = df['Applies to Buyer/Seller'].str.upper()
        df['Applies to Buyer/Seller'] = df['Applies to Buyer/Seller'].replace({'BUYER':'b', 'SELLER':'s'})
        df['Buyer/Seller code'] = df['Applies to Buyer/Seller'] 

    # Validate Buyer/Seller code column
    if len(df[df['Buyer/Seller code'].str.contains("b|s")]) == len(df):
        pass
    else:
        print(colored("WARNING:", 'red', attrs = ['bold']) +  f" {len(df) - len(df[df['Buyer/Seller code'].str.contains('b|s')])} Buyer/Seller code contains incorrect characters.")
        print(" ")


    # Excel won't allow for duplicate sheet names. 

    # if len(df[df[['Task List Name', 'Task Name']].duplicated()]) !=0:
    #     print(colored(f"WARNING: ", 'yellow') + f"{len(df[df[['Task List Name', 'Task Name']].duplicated()])} of {len(df)} Task List Name and Task Name combinations are duplicates.")
    #     print('')


    # Checking if Task List Names match sheet names
    if len(df['Task List Name'].unique()) != len(df['sheet_name'].unique()):
        mask_task = np.isin(df['Task List Name'].unique(), df['sheet_name'].unique())
        sheet_mask = np.isin(df['sheet_name'].unique(), df['Task List Name'].unique())
        print(colored(f"WARNING: ", 'yellow') + "Some of the Task List Names do not match the sheet names.")
        print(f"The Task Lists Names: {df['Task List Name'].unique()[~mask_task]} are not among the sheet names.")
        print(f"The sheet names: {df['sheet_name'].unique()[~sheet_mask]} are not among the Task List Names.")
        print('')

    # Check for duplicates
    if len(df[df.duplicated()]>0):
        print(colored("WARNING: ", 'red', attrs=['bold']) + "Duplicates found in data.")
    else:
        print(colored("GOOD: ", 'green', attrs=['bold']) + "NO duplicates found in data.")

    # Check that all tasks have an associated trigger date
    if len(df[(df['Task Name']!="") & (df['Task Trigger date \n(Relative due date)']=="")])>0:
        print(colored('DATA ERROR: ', 'red', attrs = ['bold']) + "Some tasks do not have associated trigger dates.")
        print(df[(df['Task Name']!="") & (df['Task Trigger date \n(Relative due date)']=="")]['Task Name'])
    else:
        pass
    

    print(" ")
    print(colored(f'select Name, Team_id, Status from team where Team_id = {team_id};', 'green') + ' has been added to your clipboard\nPaste into the Raw Data Tool to validate that we are working with the correct Team ID.\nVerify that the Team ID matches the ticket in JIRA.')
    clipboard.copy(f'select Name, Team_id, Status from team where Team_id = {team_id};')

    # df = df.sort_values(['Task List Name', 'Task Description', 'Task or Notification?']).reset_index(drop=True) # Don't know if I should sort these values. 
    run_list.append('1. FILE')

    if len(df[df['Applies to Buyer/Seller'] == 'BOTH (B&S)'])>0:
        print(colored("Some task lists have 'Applies to Buyer/Seller' set as 'Both (B&S)'", 'yellow', attrs =['bold']))

        df_both = df[df['Applies to Buyer/Seller'] == 'BOTH (B&S)']
        df_both.loc[df_both['Applies to Buyer/Seller'] == 'BOTH (B&S)', 'Applies to Buyer/Seller'] = 'b'
        df_both['Buyer/Seller code'] = df_both['Applies to Buyer/Seller']
        df.loc[df['Applies to Buyer/Seller'] == 'BOTH (B&S)', 'Applies to Buyer/Seller'] = 's'
        df['Buyer/Seller code'] = df['Applies to Buyer/Seller']

        df = df.append(df_both)

        if len(df[df['Applies to Buyer/Seller'] == 'BOTH (B&S)'])>0:
            print(colored("ERROR:", 'red', attrs = ['bold']) + " Could not process 'Applies to Buyer/Seller' values set as 'Both (B&S)'")
        else:
            print(colored("'Applies to Buyer/Seller' set as 'Both (B&S)' has been processed", 'green', attrs=['bold']))

            print(colored("Row values are now as follows:", 'green'))
            print(df[['Task List Name', 'Applies to Buyer/Seller']].value_counts())
            print(colored("Total Rows: ", 'green'), df[['Task List Name', 'Applies to Buyer/Seller']].value_counts().sum())
       
    else:
        print('Applies to Buyer/Seller is good.')
        pass


    return team_id, team_name, df


def get_task_lists(team_id):
    # Cell Name: Task List From Sisu

    task_list_sql_text = f"select * from client_task_list where team_id = {team_id} AND status = 'N'  ORDER BY task_list_id;"
    clipboard.copy(task_list_sql_text)
    # df_task_list_sql_text = pd.DataFrame([task_list_sql_text])
    # df_task_list_sql_text.to_clipboard(index=False,header=False)

    print(colored(f"Collecting Task Lists from Sisu for team {team_id}", attrs = ['bold']))
    print(colored("Get current Task Lists SQL has been copied to your clipboard. \nPaste this into Sisu's Raw Data Tool", 'green', attrs=['bold']))
    print(colored("Copy the returned table from the Raw Data Tool and run the following cell.", 'cyan', attrs = ['bold']))

    run_list.append('2. Task List From Sisu')



    return task_list_sql_text


def retrieve_current_task_lists_data(df):

    # 2022-06-01 Made changes so treating the combination of Task List Name and Buyer/Seller Code as unique entry. 

    # Cell Name: Insert Task Lists

    if 'df_reset_1' in locals():
        pass
    else:
        df_reset_1 = df

    '''Once the SQL query information for the existing Task Lists is copied to the clipboard, run this cell'''

    # if 'current_task_list_names' in locals():
    #     pass
    # else:
    current_task_list_names = pd.read_clipboard()
    if len(current_task_list_names) == 0: # If there are no task lists yet, the quere will return 0, in which case we need to start a blank DataFrame with the correct column names
        current_task_list_names = pd.DataFrame(columns = ['task_list_id', 'team_id', 'name', 'dscr', 'client_type_id', 'created_ts', 'updated_ts', 'status', 'display_order', 'status_trigger', 'trigger_by', 'transaction_stage_trigger'])
    else:
        pass


    return df_reset_1, current_task_list_names

def task_list_feedback(df, current_task_list_names):

    print("TASK LIST COUNT")
    print(colored(f"{len(current_task_list_names)} ", 'cyan') + "Current Task Lists")
    print(colored(f"{len((df['Task List Name']+' '+df['List Description']+' '+df['Buyer/Seller code']).unique())} ",'cyan') + "New Task Lists")
    final_task_list_count = len(current_task_list_names)+len((df['Task List Name']+' '+df['List Description']+' '+df['Buyer/Seller code']).unique())
    print(colored(f"{final_task_list_count} ", 'cyan') + "Total Task Lists")
    # Clean and add columns for the SQL insert.

    return final_task_list_count


def adding_columns(df, team_id):
    df['Team ID'] = team_id #from the folder that the file is in
    print(colored("Team ID", 'cyan') + " column added.")
    df['created_ts'] = 'current_timestamp'
    print(colored("created_ts", 'cyan') + " column added.")
    df['updated_ts'] = 'NULL'
    print(colored("updated_ts", 'cyan') + " column added.")
    df['Status'] = 'N'
    print(colored("Status", 'cyan') + " column added.")
    # df['display_order'] = [current_task_list_names['display_order'].max()+ 1 + i for i in range(0, len(df))]
    df['status_trigger'] = ''
    print(colored("status_trigger", 'cyan') + " column added.")


    return df, team_id

def define_client_task_list(df, current_task_list_names, final_task_list_count):

    # list and arrange columns for client task list SQL insert (This layout is from the VBA excel tool -- Sheet: )
    client_task_list_cols = ['Team ID', 'Task List Name', 'List Description', 'Buyer/Seller code', 'created_ts', 'updated_ts', 'Status', 'status_trigger']

    # Replace NaN values with ''
    df_client_task_list = df[client_task_list_cols].fillna('')
    df_client_task_list = df_client_task_list[-df_client_task_list[['Task List Name', 'List Description', 'Buyer/Seller code']].duplicated()].reset_index(drop = True)
    if len(current_task_list_names['display_order']) > 0: # If there are no current task lists, we start the display order at 1
        df_client_task_list['display_order'] = [current_task_list_names['display_order'].max() + 1 + i for i in range(0, len(df_client_task_list))]
    else:
        df_client_task_list['display_order'] = [1 + i for i in range(0, len(df_client_task_list))]
    client_task_list_cols_order = ['Team ID', 'Task List Name', 'List Description', 'Buyer/Seller code', 'created_ts', 'updated_ts', 'Status', 'display_order', 'status_trigger']

    # Check if the display_order is interacting as expected by checking that the final Task List's display_order number matches the expected total number of task lists. 
    if df_client_task_list['display_order'].iloc[-1] == final_task_list_count:
        # print("Finals display order equals expected Final Task List count.")
        pass
    else:
        print(colored('ERROR: Final display order does NOT equal the expected Final Task List count.', 'red', attrs=['bold']))


    return df_client_task_list, client_task_list_cols_order


def insert_task_lists(df, df_client_task_list, team_id):
    # Create TASK LISTS SQL insert statement, and save to clipboard
    task_list_values = "("+df_client_task_list['Team ID']+",'"+df_client_task_list['Task List Name']+"', '"+df_client_task_list['List Description']+"', '"+df_client_task_list['Buyer/Seller code']+"', "+df_client_task_list['created_ts']+", "+df_client_task_list['updated_ts']+", '"+df_client_task_list['Status']+"', "+df_client_task_list['display_order'].astype(str)+", '"+df_client_task_list['status_trigger']+"'),"
    df_client_task_list['task_list_values']  = task_list_values
    task_list_insert_statement ='INSERT INTO client_task_list ("team_id","name","dscr","client_type_id","created_ts","updated_ts","status","display_order","status_trigger") \nVALUES'

    string = df_client_task_list['task_list_values'].to_string(header= False, index = False)
    while "  " in string:
        string = string.replace("  ", " ")

    clipboard.copy(task_list_insert_statement + "\n" +  string.replace("\n (", "\n(").strip()[:-1] + ";")
    # clipboard.copy(task_list_insert_statement + "\n" +  df_client_task_list['task_list_values'].to_string(index = False, header = False).strip()[0:-1].replace("     ", " ").replace("    ", " ").replace('   ', ' ').replace('  ', ' ').replace(' (',  '(') + ";")
    df['Task List Name'] = df['Task List Name'].replace('   ','').replace('  ', '')

    print(' ')
    print(colored(f"Inserting Task List from the Team {team_id} template", 'white', attrs = ['bold']))
    print(colored(f"The Task List INSERT SQL from the team {team_id} template has been copied to your clipboard. \nPaste into the Sisu Raw Data Tool \nThis will load the Task Lists from the template into Sisu.", 'green', attrs=['bold']))


    run_list.append('3. Insert Task Lists')



    return df, df_client_task_list, task_list_insert_statement + "\n" +  string.replace("\n (", "\n(").strip()[:-1] + ";"


def  get_task_blueprints(team_id):
    # Cell Name: Tasks From Sisu

    task_blueprint_sql_text = f"select * from client_task_blueprint where team_id = {team_id} and status = 'N' order by task_blueprint_id;"
    clipboard.copy(task_blueprint_sql_text)
    # df_task_blueprint_sql_text = pd.DataFrame([task_blueprint_sql_text])
    # df_task_blueprint_sql_text.to_clipboard(index=False, header=False)

    print(colored(f"Collecting Task Blueprints from Sisu for team {team_id}", 'white', attrs = ['bold']))
    print(colored("Get Tasks SQL has been copied to your clipboard. \nPaste this into Sisu's Raw Data Tool", 'green', attrs=['bold']))
    print(colored("Copy the returned table from the Raw Data Tool and run the following cell.", 'cyan', attrs = ['bold']))

    run_list.append('4. Tasks From Sisu')


    return task_blueprint_sql_text


def retrieve_task_blueprints():
    # Cell Name: Process Tasks and Get Agent Info From Sisu

    '''Once SQL query for the task blueprint is copied to the clipboard, run this cell'''

    current_task_blueprint = pd.read_clipboard()

    if len(current_task_blueprint) == '0':
        current_task_blueprint = pd.DataFrame(columns = ['task_blueprint_id', 'team_id', 'name', 'dscr', 'task_type', 'display_order', 'related_client_date_column', 'due_days', 'status', 'client_type_id', 'created_ts', 'updated_ts', 'assign_to', 'email_template_id', 'email_subject', 'email_recipients'])
    else:
        pass



    return current_task_blueprint

def task_blueprint_feedback(df, current_task_blueprint):
    print("TASK COUNT")
    new_task_count = len(df)
    print(colored(f"{len(current_task_blueprint)} ", 'cyan') + "Current Tasks")
    print(colored(f"{len(df)} ", 'cyan') + "New Tasks")

    final_task_name_count = len(current_task_blueprint)+len(df)
    print(colored(f"{final_task_name_count} ", 'cyan') + "Total Tasks")

    '''Task names, types, display_orders, and descriptions'''
    client_task_blueprint_cols = ['Team ID', 'Task Name', 'Task Description', 'Task or Notification?', 'display_order', 'Trigger Date DB (Sisu)', 'Days', 'Status', 'client_type_id', 'created_ts', 'updated_ts', 'assign_to']



    return client_task_blueprint_cols, final_task_name_count, new_task_count


def get_agent_info(team_id):
    # Get agent information

    agent_info_sql_text = f"select a.first_name, a.last_name, a.agent_id from team t left join team_agent ta on t.team_id = ta.team_id left join agent a on ta.agent_id = a.agent_id where ta.team_id = {team_id} and a.status = 'N';"
    clipboard.copy(agent_info_sql_text)
    # df_agent_info_sql_text = pd.DataFrame([agent_info_sql_text])
    # df_agent_info_sql_text.to_clipboard(index=False,header=False)

    print(colored(f"Collecting Agent Information from Sisu for team {team_id}", 'white', attrs = ['bold']))
    print(colored("Get Agent SQL query has been copied to your clipboard. \nPaste this into Sisu's Raw Data Tool", 'green', attrs=['bold']))
    print(colored("Copy the returned table from the Raw Data Tool and run the following cell.", 'cyan', attrs = ['bold']))

    run_list.append('5. Process Tasks and Get Agent Info From Sisu')



    return agent_info_sql_text


def process_agent_info(df, client_task_blueprint_cols):

    # Cell Name: Insert Tasks

    '''Once the SQL query for the agent information is copied to clipboard, run this cell'''

    if 'df_reset_2' in locals():
        pass
    else:
        df_reset_2 = df

    # This cell takes in the agent information from the SQL query and creats a table to map values
    df_assign_map_general = pd.DataFrame.from_dict({
        'first_name' : ['', '', '', '', ''],
        'last_name' : ['', '', '', '', ''],
        'agent_id' : ['T', 'A', 'I', 'T', 'A'],
        'name' : ['TC', 'Agent', 'ISA', 'RECRUITER COORDINATOR', 'RECRUITER (recruit platform)'],
        'agent_key' : ['T', 'A', 'I', 'T', 'A']
    })

    df_assign_map = pd.read_clipboard()
    if len(df_assign_map) == 0:
        df_assign_map = pd.DataFrame(columns = ['first_name', 'last_name', 'agent_id'])
    else:
        pass


    df_assign_map['name'] = df_assign_map['first_name'].str.strip() + " " + df_assign_map['last_name'].str.strip()
    df_assign_map['agent_key'] = 'A'
    df_assign_map['agent_key'] = df_assign_map['agent_key'] + df_assign_map['agent_id'].astype(str)
    df_assign_map = df_assign_map.append(df_assign_map_general)

    df['Assign to TC, Agent or assignee full name'] = df['Assign to TC, Agent or assignee full name'].str.strip()
    df['Assign to TC, Agent or assignee full name'] = df['Assign to TC, Agent or assignee full name'].str.replace("  ", " ")

    df = df.merge(df_assign_map, left_on = 'Assign to TC, Agent or assignee full name', right_on = 'name', how = 'left')
    df = df.rename(columns = {'agent_key' : 'assign_to'})
    # df['name'] = df['name'].fillna('Agent')

    df = df.reset_index(drop = True)
    df['display_order'] = df.index
    # df['related_client_date_column'] = ''
    df['client_type_id'] = ''

    df_client_task_blueprints = df[client_task_blueprint_cols]
    df_client_task_blueprints = df_client_task_blueprints.fillna('')

    return df, df_reset_2, df_assign_map, df_assign_map_general, df_client_task_blueprints


def insert_task_blueprints(df_client_task_blueprints, team_id):

    # Create Tasks SQL insert statement, and save to clipboard


    task_blueprint_values = "("+df_client_task_blueprints['Team ID'].astype(str)+", '"+ df_client_task_blueprints['Task Name']+"', '"+ df_client_task_blueprints['Task Description']+"', '"+ df_client_task_blueprints['Task or Notification?']+"', "+ df_client_task_blueprints['display_order'].astype(str)+", '"+ df_client_task_blueprints['Trigger Date DB (Sisu)']+ "', "+df_client_task_blueprints['Days'].astype(str)+", '"+ df_client_task_blueprints['Status']+"', '"+ df_client_task_blueprints['client_type_id']+"', "+ df_client_task_blueprints['created_ts']+", "+ df_client_task_blueprints['updated_ts']+", '"+ df_client_task_blueprints['assign_to']+ "'),"
    df_client_task_blueprints['task_blueprint_values']  = task_blueprint_values
    task_blueprints_insert_statement = 'INSERT INTO client_task_blueprint ("team_id","name","dscr","task_type","display_order","related_client_date_column","due_days","status","client_type_id","created_ts","updated_ts","assign_to") \nVALUES'

    string = df_client_task_blueprints['task_blueprint_values'].to_string(index = False, header = False)
    while "  " in string:
        string = string.replace("  ", " ")


    clipboard.copy(task_blueprints_insert_statement + "\n" +  string.replace("\n (", "\n(").strip()[:-1] + ";")

    print(colored(f"Inserting Task Blueprints from the Team {team_id} template", 'white', attrs = ['bold']))
    print(colored(f"An INSERT statement for the Task Blueprints from the team {team_id} template has been copied to your clipboard. \nPaste into the Sisu Raw Data Tool \nThis will load the Task Blueprints from the template into Sisu.", 'green', attrs=['bold']))

    run_list.append('6. Insert Tasks')



    return task_blueprints_insert_statement + "\n" +  string.replace("\n (", "\n(").strip()[:-1] + ";"

def get_task_list_mathcup_data(team_id):

    # 4.1 - Cell Name: Get Task List Matchup

    matchup_sql_text_1 = f"select task_list_id, name, dscr, client_type_id from client_task_list where team_id = {team_id} AND status = 'N'  ORDER BY task_list_id;"

    # was: matchup_sql_text_1 = f"select task_list_id, name from client_task_list where team_id = {team_id} AND status = 'N'  ORDER BY task_list_id;"

    clipboard.copy(matchup_sql_text_1)
    # df_matchup_sql_text_1 = pd.DataFrame([matchup_sql_text_1])
    # df_matchup_sql_text_1.to_clipboard(index=False,header=False)

    print(colored(f"Collecting task_id and name from client_task_list in Sisu for team {team_id}", 'white', attrs = ['bold']))
    print(colored("SQL query has been copied to your clipboard. \nPaste this into Sisu's Raw Data Tool", 'green', attrs=['bold']))
    print(colored("Copy the returned table from the Raw Data Tool and run the following cell.", 'cyan', attrs = ['bold']))

    run_list.append("7. Get Task List Matchup")



    return matchup_sql_text_1

def retrieve_task_list_matchup_data():
    # 4.2 Cell Name: Get Task Matchup

    '''
    Once the SQL return is copied to your clipboard, run this cell

    MAKE SURE TO NOT COPY THE FOLLOWING SPACE  - WILL RESULT IN INCORRECT DELINIATION

    '''

    df_matchup_task_lists = pd.read_clipboard()
    # df_matchup_task_lists = df_matchup_task_lists[df_matchup_task_lists['task_list_id'].notna()]



    return df_matchup_task_lists


def get_task_blueprint_matchup_data(team_id):

    # 4.3
    # df_matchup_task_lists['task_list_id'] = df_matchup_task_lists['task_list_id'].astype(int)
    '''Changed the matchup SELECT statement to have 6 parameters plus the display_order parameter as the combination of the 2 cannot be duplicate'''

    matchup_sql_text_2 = f"select task_blueprint_id, display_order, name, dscr, related_client_date_column, due_days, task_type, assign_to from client_task_blueprint where team_id = {team_id} and status = 'N' order by task_blueprint_id;"

    # was : matchup_sql_text_2 = f"select task_blueprint_id, name from client_task_blueprint where team_id = {team_id} and status = 'N' order by task_blueprint_id;"

    clipboard.copy(matchup_sql_text_2)

    # df_matchup_sql_text_2 = pd.DataFrame([matchup_sql_text_2])
    # df_matchup_sql_text_2.to_clipboard(index=False,header=False)

    print(colored(f"Collecting task_blueprint_id and name from client_task_blueprint in Sisu for team {team_id}", 'white', attrs = ['bold']))
    print(colored("Get Tasks SQL has been copied to your clipboard. \nPaste this into Sisu's Raw Data Tool", 'green', attrs=['bold']))
    print(colored("Copy the returned table from the Raw Data Tool and run the next cell.", 'cyan', attrs = ['bold']))

    # df_matchup_task_lists = df_matchup_task_lists[['name', 'dscr', 'client_type_id']].drop_duplicates().join(df_matchup_task_lists['task_list_id'], how='left').reset_index(drop=True)

    # display(df_matchup_task_lists)

    run_list.append('8. Get Task Matchup')




def retrieve_task_blueprint_matchup_data(df):

    # 4.4
    # Cell Name: Process and Insert Matchup

    if 'df_reset_3' in locals():
        pass
    else:
        df_reset_3 = df

    '''Once SQL query is copied to clipboard, run this cell'''

    df_matchup_task_blueprint = pd.read_clipboard()



    return df_reset_3, df_matchup_task_blueprint


def clean_and_process_matchup_data(df, df_matchup_task_blueprint, df_matchup_task_lists):

    # 4.5
    # df_matchup_task_blueprint = df_matchup_task_blueprint[df_matchup_task_blueprint['task_blueprint_id'].notna()]

    # df_matchup_task_blueprint['task_blueprint_id'] = df_matchup_task_blueprint['task_blueprint_id'].astype(int)

    # df_matchup_task_blueprint = df_matchup_task_blueprint[['name', 'dscr', 'related_client_date_column', 'due_days', 'task_type', 'assign_to']].drop_duplicates().join(df_matchup_task_blueprint['task_blueprint_id'], how='left').reset_index(drop=True)

    df['Task Name'] = df['Task Name'].str.replace(r'\(', ' ').str.replace(r'\)',' ' ).str.replace('  ', ' ')
    df_matchup_task_blueprint['name'] = df_matchup_task_blueprint['name'].str.replace(r'\(',  ' ').str.replace(r'\)',' ').str.replace('  ', ' ')

    df = df.fillna('')
    df_matchup_task_lists = df_matchup_task_lists.fillna('')
    df_matchup_task_blueprint = df_matchup_task_blueprint.fillna('')



    return df, df_matchup_task_lists, df_matchup_task_blueprint



def merge_and_remove_duplicated_tasks(df_matchup_task_blueprint, df, df_matchup_task_lists, new_task_count):
    df_matchup_task_blueprint['due_days'] = df_matchup_task_blueprint['due_days'].astype(str).fillna('0')
    df_matchup_task_lists = df_matchup_task_lists.fillna("")
    df_matchup_task_blueprint = df_matchup_task_blueprint.fillna("")
    df_merge_check = df.merge(df_matchup_task_lists, left_on = ['Task List Name', 'List Description', 'Buyer/Seller code'], right_on = ['name', 'dscr', 'client_type_id'] , how = 'left').merge(df_matchup_task_blueprint, left_on = ['Task Name', 'Trigger Date DB (Sisu)', 'Days', 'Task or Notification?', 'assign_to', 'display_order'] , right_on = ['name', 'related_client_date_column', 'due_days', 'task_type', 'assign_to', 'display_order'], how = 'left').drop('index', axis = 1)
    print("Number of Tasks before removing duplicates: ", len(df_merge_check))
    if len(df_merge_check)%new_task_count == 0:
        print("Number of duplications: ", len(df_merge_check)/new_task_count)
    
    merge_check_columns = df_merge_check.columns[~df_merge_check.columns.str.contains('task_list_id|task_blueprint_id')]

    return df_merge_check[merge_check_columns].drop_duplicates(keep='last').merge(df_merge_check[['task_list_id', 'task_blueprint_id']], left_index = True, right_index = True)



def test_merge(new_task_count, df_matchup_task_blueprint, df_matchup_task_lists, df):

    ''' Merging Tasks on these 6 parameters. These can be duplicates. Need something else...'''

    # df.merge(df_matchup_task_blueprint, left_on = ['Task Name', 'Task Description', 'Task Trigger date \n(Relative due date)', 'Days', 'Task or Notification?', 'assign_to'] , right_on = ['name', 'dscr', 'related_client_date_column', 'due_days', 'task_type', 'assign_to'], how = 'left')

    '''also cannot use display order'''

    # df.merge(df_matchup_task_blueprint, left_index = True , right_on = ['display_order'], how = 'left')

    '''
    Maybe the 6 parameters and the display order will work as these values are less likely to be duplicate. 
    Can still be duplicate if using the same data a second or third time.
    You can tell that this is occuring if the count of the rows is a multiple of the expected rows. 
    Each duplicate will then have unique task_list_id and task_blueprint_id.


    My fix is to 
    1. remove task_list_id and task_blueprint_id columns
    2. remove duplicates
    3. merge the task_list_id and task_blueprint_id values to the data that has had the duplicates removed. 

    NOTE: drop_duplicates has to have the options 'keep' set to 'last' or the task_list_id/task_blueprint_id combo will be a duplicate in sisu. 

    '''
    print(colored("Expected Number of Tasks: ", 'cyan', attrs=['bold']) + f'{new_task_count}')

    df_merge_funct_test = merge_and_remove_duplicated_tasks(df_matchup_task_blueprint, df, df_matchup_task_lists, new_task_count)

    # df_merge_check = df.merge(df_matchup_task_lists, left_on = ['Task List Name', 'List Description', 'Buyer/Seller code'], right_on = ['name', 'dscr', 'client_type_id'] , how = 'left').merge(df_matchup_task_blueprint, left_on = ['Task Name', 'Trigger Date DB (Sisu)', 'Days', 'Task or Notification?', 'assign_to', 'display_order'] , right_on = ['name', 'related_client_date_column', 'due_days', 'task_type', 'assign_to', 'display_order'], how = 'left').drop('index', axis = 1)
    # merge_check_columns = df_merge_check.columns[~df_merge_check.columns.str.contains('task_list_id|task_blueprint_id')]
    # print('Number of Tasks after removing duplicates: ', len(df_merge_check[merge_check_columns].drop_duplicates().merge(df_merge_check[['task_list_id', 'task_blueprint_id']], left_index = True, right_index = True)))

    print('Number of Tasks after removing duplicates: ', len(df_merge_funct_test))

    # display(df_merge_check[merge_check_columns].drop_duplicates().merge(df_merge_check[['task_list_id', 'task_blueprint_id']], left_index = True, right_index = True))
    # display(df_merge_funct_test)






def merge_data(df_matchup_task_blueprint, df, df_matchup_task_lists, new_task_count):
    df_reset_4 = df

    # The following 2 lines were commented out during version 7
    # df = df.merge(df_matchup_task_lists, left_on = ['Task List Name', 'List Description', 'Buyer/Seller code'], right_on = ['name', 'dscr', 'client_type_id'] , how = 'left')
    # df = df.merge(df_matchup_task_blueprint, left_on = ['Task Name', 'Trigger Date DB (Sisu)', 'Days', 'Task or Notification?', 'assign_to', 'display_order'] , right_on = ['name', 'related_client_date_column', 'due_days', 'task_type', 'assign_to', 'display_order'], how = 'left')

    df = merge_and_remove_duplicated_tasks(df_matchup_task_blueprint, df, df_matchup_task_lists, new_task_count)

    df = df.reset_index(drop = True)



    return df, df_reset_4


def validate_merge(df):

    # Validate matchup values (and make sure the id values are integers)

    if len(df[df['task_list_id'].isna()]) > 0:
        print(colored("ERROR: ", 'red', attrs=['bold']) + "Missing " + colored("task_list_id", 'cyan') + " for the following Tasks:")
        print(df[df['task_list_id'].isna()]['Task Name'])
        
    else:
        df['task_list_id'] = df['task_list_id'].astype(int)
        print(colored("No Null values for Task List ID", 'green'))



    if len(df[df['task_blueprint_id'].isna()]) > 0:
        print(colored("ERROR: ", 'red', attrs=['bold']) + "Missing " + colored("task_blueprint_id", 'cyan') + " for the following Tasks:")
        print(df[df['task_blueprint_id'].isna()]['Task Name'])
        
    else:
        
        df['task_blueprint_id'] = df['task_blueprint_id'].astype(int)
        print(colored("No Null values for Task Blueprint ID", 'green'))



def create_merge_insert_statement(df, team_id):
    df['task_list_id'] = df['task_list_id'].astype(int)
    df['task_blueprint_id'] = df['task_blueprint_id'].astype(int)
    df_matchup = df[['task_list_id', 'task_blueprint_id']]
    df_matchup['display_order'] = df.index

    # Create SQL insert statement, and save to clipboard
    task_list_blueprint_matchup_values = "("+df_matchup['task_list_id'].astype(str)+","+ df_matchup['task_blueprint_id'].astype(str)+","+ df_matchup['display_order'].astype(str)+ "),"
    df_matchup['task_list_blueprint_matchup_values']  = task_list_blueprint_matchup_values


    task_list_blueprints_matchup_insert_statement = 'INSERT INTO client_list_task_blueprint ("task_list_id","task_blueprint_id","display_order") \nVALUES'

    string = df_matchup['task_list_blueprint_matchup_values'].to_string(index = False, header = False)
    while "  " in string:
        string = string.replace("  ", " ")

    clipboard.copy(task_list_blueprints_matchup_insert_statement + "\n" +  string.replace("\n (", "\n(").strip()[:-1] + ";")
    # clipboard.copy(task_list_blueprints_matchup_insert_statement + "\n" +  df_matchup['task_list_blueprint_matchup_values'].to_string(index = False, header = False).strip().replace('   ', '  ').replace('  ', ' ').replace(' (', '(')+ ";")


    print(colored(f"Inserting Matchup data for Team {team_id}", 'white', attrs = ['bold']))
    print(colored(f"An INSERT statement for the Matchup data for Team {team_id} has been copied to your clipboard. \nPaste into the Sisu Raw Data Tool \nThis will load the Matchup data into Sisu.", 'green', attrs=['bold']))

    run_list.append('9. Process and Insert Matchup')



    return task_list_blueprints_matchup_insert_statement + "\n" +  string.replace("\n (", "\n(").strip()[:-1] + ";"


def create_summary(current_task_list_names, current_task_blueprint, df):

    # Cell Name: Summary

    summary_data = {
        'Initial Task List Count' : [len(current_task_list_names)],
        'New Task List Count' : [len(df['Task List Name'].unique())],
        'Total Task List Count': [len(current_task_list_names) + len(df['Task List Name'].unique())],
        'Initial Task Count' : [len(current_task_blueprint)],
        'New Task Count': [len(df)],
        'Total Task Count': [len(current_task_blueprint) + len(df)+ ' \n']
    }
    df_summary = pd.DataFrame.from_dict(summary_data)

    print(colored("SUMMARY", 'cyan'))
    print(colored("Copy the white text below and paste it into the following markdown cell. Run the markdown cell, select the output, copy it, and paste into JIRA.", 'green'))
    clipboard.copy(df_summary.T.reset_index().rename(columns = {'index':'Subject', 0:'Count'}).to_markdown(index = False))
    print(df_summary.T.reset_index().rename(columns = {'index':'Subject', 0:'Count'}).to_markdown(index = False))

    run_list.append('10. Summary')

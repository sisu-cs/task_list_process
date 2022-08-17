![Sisu](https://global-uploads.webflow.com/5f4444910aa0ad6a50bb4f52/5f444fb00e4dc15dd0f0416e_sisu-logo.svg)

# <span style = "color:#4287f5">Task List Template Processing Tool </span>

The goal of this tool is to import a Sisu Task List Template xlsx file that has been filled out by a client and 
- validate that the required information is present
- return SQL scripts at intervals to both retrieve information from the Sisu API and insert new information from the template. 

Because of necessary pauses in the process, due to the need to manually interact with the Sisu SQL data tool, this tool as been
formatted as a notebook. 

There is an associated python script that is called in the notebook to increase the usability of the notebook by cutting down on the 
vast amount of code in each cell. 

## Requirements

See the [requirements.txt](https://github.com/sisu-cs/task_list_process/blob/main/requirements.txt)

If you don't already have jupyter notebook, or jupyter lab, installed, I recommend downloading [anaconda](https://www.anaconda.com/).
It comes with most needed packages as well as other really useful data tools and IDEs. 

Jupyter Documentation can be found [here](https://docs.jupyter.org/en/latest/).

[task_list_tools.py](https://github.com/sisu-cs/task_list_process/blob/main/task_list_tools.py) has to be in the same folder as the notebook. 

## How to use

The markdown cells that precede each code cell are titled to be descriptive of the process in the code cell. 
The markdown for each cell is marked with a number representing order. 

0. Library
    - Run this cell to import library
1. Select Client Template File, View Lists & Tasks and Clean & Fixes 
    - This cell will prompt a window. Select the xlxs file you wish to import. 
2. Collect Current Task Lists
    - This cell will copy an SQL query to the clipboard for selecting the current Task List.
    - Paste the query into the Raw Data Tool. 
3. Task List Insert
    - If the query returns a table, copy it to your clipboard before running this cell.
      - This cell will retreive what is copied to your clipboard when executed. 
      - If there is nothing copied to your clipboard it will treat it as an empy table. 
    - This cell will return a SQL statement for INSERTing the new task lists. 
    - It will also return infromation about number of current tasks lists and new task lists. 
4. Collect Current Task Blueprints
    - This cell will copy an SQL query to the clipboard for selecting the current Task Blueprints. 
    - Paste the query into the Raw Data Tool
5. Retrieve Task Blueprints & Collect Agent Information
    - Copy the table that populates in the Raw Data Tool to your clipboard before running this cell. 
    - This cell will return an SQL query for the agent information. 
    - Paste the query into the Raw Data Tool.
    - This cell also returns information about the number or current, and new, task blueprints. 
6. Retrieve Agents & Insert Task Blueprints
    - Copy the table that populates in the Raw Data Tool to your clipboard before running this cell. 
    - This cell will produce an SQL statement for INSERTing the new task blueprints. 
7. Collect Task List Matchup Data
    - This cell will copy an SQL query to the clipboard for collecting the Task List Matchup Data. 
8. Retrieve Task List IDs & Collect Task Blueprint IDs
    - Copy the table that populates in the Raw Data Tool to your clipboard before running this cell. 
    - This cell will copy an SQL query to the clipboard for collecting the Task Blueprint Matchup Data. 
9. Retrieve Task Blueprint IDs & Build the Lists-Tasks Matchup (Merge)
    - Copy the table that populates in the Raw Data Tool to your clipboard before running this cell. 
    - This cell merges the matchup data about serveral [parameters](https://github.com/sisu-cs/task_list_process/blob/26f61da0606c0ac63b2d7cbe6b266b987f04a9ec/task_list_tools.py#L765).
10. Validate Merge
    - This cell checks if the columns for the Task List IDs and the Task Blueprint IDs in the DataFrame that is returned from the merge are complete (No NA values).
    - If there are NA values, then there may be special characters in the DataFrame than are not supported (and thus changed) in the SISU API. 
      - If the number of rows with missing data is low, the fix can be done manually (for now). This item is already reported as an [issue](https://github.com/sisu-cs/task_list_process/issues/3).
11. Build the Matchup Insert Statement
     - This cell creates a matchup SQL INSERT statement and copies it to the clipboard. 
     - Paste this into the Raw Data Tool. 
12. Summary
    - This cell outputs a table with the initial, added, and total Task List count and Task Blueprint count in markdown text. 




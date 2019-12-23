#Imports 
import subprocess
import sys
from pip._internal import main as pip
import pathlib
import importlib 
import os
import ipywidgets as widgets


def install(package):
    pip(['install', '--user', package])
    
install("canvasapi")
install("python-dotenv")



try:
    from dotenv import load_dotenv
    import dotenv
    import os
    import os.path
    from canvasapi import Canvas
except:
    os._exit(00)
    print("please go back and run the install file")
    
#Variables 

API_URL = 'https://canvas.ubc.ca/'
COURSE_KEY= 44564 #40476
ASSIGNMENT_KEY = 362680 #356269
ALL_FILES = ['assignment.ipynb']   #Put your file names here as a list of strings. es: ["file1.ipynb", "testcsv.csv"]
token_success = False
API_KEY=""

def touch_path(path_str):
    """
    Run the equivalent of UNIX touch on path_str, where path_str
    can contain ~ to refer to the user's home directory, managed
    via Path.expanduser. Touches with user read/write permission
    and tries to deny group/other permissions.
    """
    envp = pathlib.Path(path_str). expanduser()
    envp.touch(0o600)

#Token Verification:
def token_verif(course = COURSE_KEY):
    try:
        touch_path("~/.env")   
        load_dotenv()
        global API_KEY
        API_KEY= os.getenv("API_KEY")
        canvas = Canvas(API_URL, API_KEY)
        course_got = canvas.get_course(course)
        global token_success
        token_success = True
        
        
    except:
        print("We can't seem to find your token, blah blah blah, put it in now:")
        token = input()
        
        while "API_KEY" in os.environ:
            del os.environ["API_KEY"]
            os.remove(os.path.expanduser("~/.env"))
            touch_path("~/.env") 
        
                
        with open(os.path.expanduser("~/.env"), "a") as f:
            f.write("\nAPI_KEY = " + token)
        try: 
            load_dotenv()
            API_KEY= os.getenv("API_KEY")
            print(API_KEY)
            canvas = Canvas(API_URL, API_KEY)
            course = canvas.get_course(COURSE_KEY)
            print("got here as well")
            token_success = True 
            
        except:
            print("Oh no! something didn't work, please complain to Steve")
        
def convert_notebook_to_html( file_name: str, notebook_path: str = "", allow_errors: bool = False) -> bool: 
    try: 
        if allow_errors: 
            outp= subprocess.run(["jupyter", "nbconvert",   "--execute", "--allow-errors", "--to",  "html",  file_name], capture_output= True)
        else:
            outp= subprocess.run(["jupyter", "nbconvert",   "--execute", "--to",  "html",  file_name], capture_output= True)
            
        print(outp.stdout.decode("ascii"))
        return True 
    
    except: 
        
        return False 
            
def file_ipynb(file_name: str):
    return file_name[-6:] == ".ipynb"

def file_csv(file_name: str):
    return file_name[-4:] == ".ipynb"

        
def submit_assignment(files=ALL_FILES,assign =ASSIGNMENT_KEY, c=COURSE_KEY ):
    canvas = Canvas(API_URL, API_KEY)
    course = canvas.get_course(c)
    assignment = course.get_assignment(assign)
    submit_these_id = []
    for file in files:
        chtml= convert_notebook_to_html(file_name = file)
        if chtml: 
            file1 = assignment.upload_to_submission(file)
            if file_ipynb(file):
                    file2 = assignment.upload_to_submission(file[:-6] + '.html')
            elif file_csv(file):
                    file2 = assignment.upload_to_submission(file[:-4] + '.html')
            submit_these_id.append(file1[1]['id'])
            submit_these_id.append(file2[1]['id'])
        else:
            print("This file has an error. Do you still want to submit this file?")
            answ = input()
            if answ:
                chtml = convert_notebook_to_html(file_name = file, allow_errors = True)
                file1 = assignment.upload_to_submission(file)
                if file_ipynb(file):
                    file2 = assignment.upload_to_submission(file[:-6] + '.html')
                elif file_csv(file):
                    file2 = assignment.upload_to_submission(file[:-4] + '.html')
                submit_these_id.append(file1[1]['id'])
                submit_these_id.append(file2[1]['id'])
            else: 
                exit()
                
        
    
    submission = assignment.submit({ 'submission_type' : 'online_upload', 'file_ids' : submit_these_id})
    print("check your submission here: " + submission.preview_url)
    
#interface definition  

ALL_FILES =['assignment.ipynb', "a", "b"]

token = widgets.Valid(
        value=token_success,
        description='Token')

course_menu = widgets.Dropdown(
       options=['CS103_2018W1', 'CS103_2018W2', 'CS103_2019W1'],
       value='CS103_2019W1',
       description='Course:')
asn_menu = widgets.Dropdown(
       options=['Module 1 tutorial', 'Module 2 tutorial','Module 3 tutorial', 'Module 4 tutorial', 
                'Module 5 tutorial','Module 6 tutorial','Module 7 tutorial', 'Module 8 tutorial', 'Project submission'],
       value='Module 2 tutorial',
       description='Assignment:')
files = widgets.SelectMultiple(
        options=ALL_FILES,
        value=[],
        #rows=10,
        description='Files',
        disabled=False)
button = widgets.Button(
    description='submit',
    disabled=False,
    button_style='', # 'success', 'info', 'warning', 'danger' or ''
    tooltip='submit',
    icon='check')
missing_token = widgets.Text(
    value='',
    placeholder='Your token here',
    description='Token:',
    disabled=False)


t = token
cm = course_menu
am = asn_menu
f = files
b = button
mt = missing_token

def submit_selected(event):
    assign= list(f.value)
    submit_assignment(files=assign)

def submit():  
    if token_success:
        display(t,cm, am,f,b)
        b.on_click(submit_selected)
    else:
        token_verif()
        global token
        token = widgets.Valid(value=token_success,description='Token')
        to = token
        display(to,cm, am,f,b)
        b.on_click(submit_selected)
    

# be aware that the overall cs103 library has its own __all__
__all__ = [
    "submit"
]


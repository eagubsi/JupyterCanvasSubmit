#Imports 
import subprocess
import sys
from pip._internal import main as pip
import pathlib
import importlib 
import os
import ipywidgets as widgets
import glob
import tempfile
import shutil
from IPython.display import Javascript


def install(package):
    pip(['install', '--user', package])
    

try:
    import os
    import os.path
    from canvasapi import Canvas
    from dotenv import load_dotenv
except:
    print("Attempting to install canvasapi:")
    install("canvasapi")
    print("Attempting to install python-dotenv:")
    install("python-dotenv")
    print("Exiting kernel to force a restart now that installs are complete:")
    os._exit(1) 

#Variables 

API_URL = 'https://canvas.ubc.ca/'
ALLOWED_EXTENSIONS = ['ipynb', 'csv']
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
def token_verif(course):
    def test_token():
        #Attempts to access the token in the .env 
        #file and access the course with that token
        touch_path("~/.env")   
        load_dotenv()
        global API_KEY
        API_KEY= os.getenv("API_KEY")
        canvas = Canvas(API_URL, API_KEY)
        course_got = canvas.get_course(course)
        global token_success
        token_success = True
        
    try:
        test_token()
    
    except:
        print("We can't seem to find your token, if you need help finding it please see:")
        print("https://documentcloud.adobe.com/link/track?uri=urn%3Aaaid%3Ascds%3AUS%3A5a18408c-2102-4dc5-8f50-f8205f9b85bf")
        print("Please copy and paste your token here and then hit enter:")
        token = input()
        
        #If API key is incorrect in the .env file, we want to delete the 
        #line with the API key, however right now it just deletes the entire .env file
        if "API_KEY" in os.environ:
            del os.environ["API_KEY"]
            os.remove(os.path.expanduser("~/.env"))
            touch_path("~/.env") 
        
                
        with open(os.path.expanduser("~/.env"), "a") as f:
            f.write("\nAPI_KEY = " + token)
        
        try: 
            test_token()
            
        except:
            print("We are still unable to access your course, please submit manually, then bring this up with a TA or instructor.")
        
def convert_notebook_to_html( file_name: str, notebook_path: str = "", allow_errors: bool = False) -> bool:  
    
    if allow_errors: 
        outp= subprocess.run(["jupyter", "nbconvert",   "--execute", "--allow-errors", "--to",  "html",  file_name], capture_output= True)
    else:
        outp= subprocess.run(["jupyter", "nbconvert",   "--execute", "--to",  "html",  file_name], capture_output= True)
     
    convert_success = outp.returncode == 0 
    
    if not convert_success:
        print(outp.stderr.decode("ascii"))
        
    return convert_success 
     
     
            
def file_ipynb(file_name: str):
    return file_name[-6:] == ".ipynb"

def file_csv(file_name: str):
    return file_name[-4:] == ".csv"

        
def submit_assignment(files, assign, c, allow_errors = False ):
    canvas = Canvas(API_URL, API_KEY)
    course = canvas.get_course(c)
    assignment = course.get_assignment(assign)
    submit_these_id = []
    for file in files:
        chtml= convert_notebook_to_html(file_name=file, allow_errors= allow_errors)
        
        def prep_files():
            file1 = assignment.upload_to_submission(file)
            if file_ipynb(file):
                file2 = assignment.upload_to_submission(file[:-6] + '.html')
            elif file_csv(file):
                file2 = assignment.upload_to_submission(file[:-4] + '.html')
            submit_these_id.append(file1[1]['id'])
            submit_these_id.append(file2[1]['id'])
        
        if chtml: 
            prep_files()
        else:
            return False
                
    
    submission = assignment.submit({ 'submission_type' : 'online_upload', 'file_ids' : submit_these_id})
    print("Your assignment was submitted succesfully!")
    print("However unsaved changes may not have been submitted.")
    print("Please check your submission at this link: " + submission.preview_url)
    print("It will be easiest to check your submission using the HTML file at that link.")
    return True
    
def submit_assignment_in_temp(files, assign , c, allow_errors = False ):
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tempdir:
        try:
            for file in files:
                shutil.copy(file, tempdir)
            os.chdir(tempdir)
            return submit_assignment(files, assign, c, allow_errors)
        finally:
            os.chdir(cwd)

#interface definition  

def token_widget():
    token = widgets.Valid(
            value=token_success,
            description='Token')
    return token

def course_menu_widget():
    course_menu = widgets.Dropdown(
           options=['CS103_2018W1', 'CS103_2018W2', 'CS103_2019W1'],
           value='CS103_2019W1',
           description='Course:')
    return course_menu

def asn_menu_widget():
    asn_menu = widgets.Dropdown(
           options=['Module 1 tutorial', 'Module 2 tutorial','Module 3 tutorial', 'Module 4 tutorial', 
                    'Module 5 tutorial','Module 6 tutorial','Module 7 tutorial', 'Module 8 tutorial', 'Project submission'],
           value='Module 2 tutorial',
           description='Assignment:')
    return asn_menu

def files_widget():
    all_files = [file for ext in ALLOWED_EXTENSIONS for file in glob.glob('*.' + ext)]
    files = widgets.SelectMultiple(
            options=all_files,
            value=[all_files[0]],
            #rows=10,
            description='Files',
            disabled=False)
    return files

def submit_button_widget():
    button = widgets.Button(
        description='submit',
        disabled=False,
        button_style='', # 'success', 'info', 'warning', 'danger' or ''
        tooltip='submit',
        icon='check')
    return button

def allow_error_button_widget():
    button = widgets.Button(
        description='Submit even if there are errors',
        layout=widgets.Layout(width='50%', height='80px'),
        disabled=False,
        button_style='', # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Submit even if there are errors',
        icon='check')
    return button

def missing_token_widget():
    missing_token = widgets.Text(
        value='',
        placeholder='Your token here',
        description='Token:',
        disabled=False)
    return missing_token

def try_save():
    """
    This wasn't saving consistently :(
    We think it would work if it were on the main thread. 
    
    Attempts to save current notebook, 
    otherwise prints an informative error message
    """
    try:
        Javascript("IPython.notebook.save_notebook()")
    except:
        print("""We tried to automatically save your notebook, in case you are submitting it.
        But something didn't work, please make sure to save your notebook before submitting.
        We will continue with the files as they are now.""")
        

def submit(course_key:int, assign_key:int)-> None:
    """
    
    """
    t = token_widget()
    cm = course_menu_widget()
    am = asn_menu_widget()
    f = files_widget()
    b = submit_button_widget()
    mt = missing_token_widget()
    aebw= allow_error_button_widget()
    
    def submit_selected(button):
            
            files= list(f.value)
            
            if len(files)<1:
                    print("No files have been selected. Please pick the files you would like to submit and try again.")
                    return 
                
            allow_errors = button == aebw
            
            try:
                success = submit_assignment_in_temp(files, assign_key, course_key, allow_errors)
                if not success and not allow_errors:
                    print("ERROR!")
                    print("We attempted to submit these selected files:")
                    print(", ".join(files))
                    print("A jupyter notebook in the submission caused an error.")
                    print("If you really want to submit this assignment with the errors please click" +
                          " the \"Submit even if there are errors\" button")  
                    display(aebw)
                elif not success:
                    print("We are still unable to submit your assignment, please submit your assignment manually.")
                    print("Also please bring this issue to the attention of a TA or professor")
            except:
                print("ERROR! Something went wrong with accessing Canvas for course key " + str(course_key) +
                      ", assignment key " + str(assign_key) + ", files:")
                print(", ".join(files))
                print("and your token.")
                print("Please submit manually and ask a member of course staff for help")
            
    if token_success:
        display(t,f,b)
    else:
        token_verif(course_key)
        to= token_widget()
        display(to,f,b)
        
    b.on_click(submit_selected)
    aebw.on_click(submit_selected)
    
    
    

# be aware that the overall cs103 library has its own __all__
__all__ = [
    "submit"
]
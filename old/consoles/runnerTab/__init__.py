from abstract_utilities import call_for_all_tabs,get_caller_dir
call_for_all_tabs(get_caller_dir())
from .main import runnerTab
from abstract_gui import startConsole
def startRunnerConsole():
    startConsole(runnerTab)

from src.abstract_react import *
from old import *
startReactRunnerConsole()
root = "/var/www/TDD/my-app"
abs_path = os.path.abspath(__name__)
dirname = os.path.dirname(abs_path)
dot_path = os.path.join(dirname,"graph.dot")
out_path = os.path.join(dirname,"import-graph.json")
project_root = '/var/www/TDD/my-app'
scope = 'all'
entries = ["index", "main"]  # GUI can override
analyzer = start_analyzer(root=root,dot=dot_path,out=out_path)

graph_wrkr = ImportGraphWorker(
        project_root=project_root,
        scope=scope,
        entries=entries
        
    )
graph_wrkr.run()
input(graph_wrkr.graph)

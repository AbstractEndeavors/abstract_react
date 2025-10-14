from src.abstract_react import run_build_get_errors, get_entry_output,run_autofix_build,run_build


project_dir = "/var/www/presites/abstractendeavors/react/main"
build_get_errors = run_build(path=project_dir, user_at_host="solcatcher", use_tsc=True, install_first=False)
input(build_get_errors)

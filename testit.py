from src.abstract_react import run_build_get_errors, get_entry_output,run_autofix_build


project_dir = "/var/www/presites/typicallyoutliers/react/loopzys"
run_autofix_build(path=project_dir, build_cmd="yarn build", auto=False, use_tsc=False)


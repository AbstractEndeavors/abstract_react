import argparse,json,os,re,traceback,shlex,subprocess
from pathlib import Path
from typing import *

from abstract_utilities.file_utils import (
    define_defaults,
    collect_filepaths,
    make_allowed_predicate,
    make_list,
    get_media_exts
    )
from abstract_utilities import make_list
from abstract_apis import run_local_cmd,run_remote_cmd

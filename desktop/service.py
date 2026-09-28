import runpy,sys
from pathlib import Path
root=Path(__file__).resolve().parent
log=(root/'service.log').open('a',encoding='utf-8',buffering=1)
sys.stdout=log;sys.stderr=log
runpy.run_path(str(root/'server.py'),run_name='__main__')

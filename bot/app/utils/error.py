import sys
import os

def exception_with_line():
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(".")
    print(exc_type, fname, exc_tb.tb_lineno)
    print(".")
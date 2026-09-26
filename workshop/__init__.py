"""Support code for the marimo notebooks in ../notebooks.

Only code that must live in a real module is here:
  * functions sent to process pools (they are pickled by module + name)
  * servers that the notebooks start as subprocesses
  * child programs for the subprocess notebook
  * database setup
"""

"""
Exclude setup.py from pytest
----------------------
However, many projects will have a setup.py which they don't want to be imported.
For such cases you can dynamically define files to be ignored
by listing them in a conftest.py file:
@@from_url=https://docs.pytest.org/en/stable/example/pythoncollection.html#:~:text=Ignore%20paths%20during%20test%20collection&text=The%20%2D%2Dignore%2Dglob%20option,'*_01.py'%20.]
"""

collect_ignore = ["setup.py"]

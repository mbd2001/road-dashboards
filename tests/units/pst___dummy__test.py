""" Dummy test always should pass
Can be used for testing pytest configuration
"""

import sys

from loguru import logger

from road_dashboards import dummy_main_module


def test_dummy():
    """
    # In this dummpy test we will also take a look
    # at how you ensure you are tesating the **intalled** package when you want to
    """
    logger.info(f"Note that PyTest changes sys.path: {sys.path}")
    logger.info(f"Your imported package is from: {dummy_main_module.__file__}")
    """
    # ---- AAA Method ---
    # this is a standard format of a test -

    # 1.arrange [prepare,  declare the expected result]
    #
    """
    expected = True
    """
    # 2.act [get the actual result]
    """
    actual = dummy_main_module.dummy_main()
    """
    # 3.assert [verify actual vs expectued]
    """
    assert actual == expected

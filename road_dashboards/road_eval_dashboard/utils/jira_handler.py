from datetime import datetime

from jira import JIRA

MAX_ISSUE_KEY_DIGITS = 5
ME_JIRA_SERVER = "https://jira.mobileye.com"
USER = "s_s_sys_road"
TOKEN = "HAxRuBpy8LevVUlgN4F267rDAKrLDygur1coJR"
jira_client = None


def get_jira_client():
    global jira_client
    if jira_client is not None:
        return jira_client
    return JIRA(
        options={"server": ME_JIRA_SERVER, "verify": "/etc/ssl/certs/ca-certificates.crt"},
        basic_auth=(USER, TOKEN),
    )


def add_comment_to_jira(issue_key: str, comment: str):
    """

    Args:
        issue_key: jira issue key - for example ROAD-4123
        comment: comment to be added to jira

    Returns:

    """
    jira = get_jira_client()
    issue = jira.issue(issue_key)
    comment_obj = jira.add_comment(issue, comment)

    return comment_obj


def add_attachment(issue_key: str, attachment: str, name=None):
    """

    Args:
        issue_key: jira issue key - for example ROAD-4123
        attachment: a path to attachment file
        name: name that will show in jira attachments

    """
    jira = get_jira_client()
    jira.add_attachment(issue=issue_key, attachment=attachment, filename=name)


def add_image_in_comment(issue_key: str, image_path: str, name: str = None, comment: str = ""):
    """

    Args:
        issue_key: jira issue key - for example ROAD-4123
        image_path: path to image file
        name: name that will show in jira attachments
        comment: additional comment to image
    """

    if name is None:
        name = "image_" + datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + ".jpg"
    add_attachment(issue_key, image_path, name)

    comment = comment + f"\n!{name}!"
    add_comment_to_jira(issue_key, comment)

    return


def get_jira_issues_from_prefix(prefix):
    if not prefix:
        return []
    jira = get_jira_client()
    split_prefix = prefix.split("-")
    if len(split_prefix) > 1 and split_prefix[0] == "ROAD" and split_prefix[1].isdigit():
        tickets = search_issues_by_prefix(jira, split_prefix)
    else:
        tickets = search_issues_by_summary(jira, prefix)
    return tickets


def search_issues_by_summary(jira, prefix):
    tickets = jira.search_issues(
        f'summary ~ "{prefix}" AND project=ROAD ORDER BY resolution, status, updated DESC', fields=["summary"]
    )
    return tickets


def search_issues_by_prefix(jira, split_prefix):
    or_condition = get_prefix_conditions(split_prefix)
    if or_condition == "":
        return []
    tickets = jira.search_issues(f"({or_condition}) AND project=ROAD ORDER BY issuekey", fields=["summary"])
    return tickets


def get_prefix_conditions(split_prefix, max_issue_key_digits=MAX_ISSUE_KEY_DIGITS):
    """
    issuekey is not a text field so we cannot perform contain operation on it, so in this function we create conditions
    to search all issues with issuekey between prefix * 10 and (prefix + 1) * 10, prefix * 100 and (prefix + 1) * 100
    and etc... for example for prefix ROAD-56 we will search all issues with issuekey beyween 560 to 570 and 5600 to 5700
    :param split_prefix:
    :param max_issue_key_digits:
    :return:
    """
    prefix_num = int(split_prefix[1])
    num_to_multiply = len(split_prefix[1])
    or_condition = ""
    multiplier = 1
    for _ in range(num_to_multiply + 1, max_issue_key_digits):
        multiplier *= 10
        if or_condition != "":
            or_condition += " OR "
        or_condition += (
            f'(issuekey >= "ROAD-{prefix_num * multiplier}" AND issuekey < "ROAD-{(prefix_num + 1) * multiplier}")'
        )
    return or_condition

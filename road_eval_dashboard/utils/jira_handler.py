from datetime import datetime

from jira import JIRA

ME_JIRA_SERVER = "https://jira.mobileye.com"
USER = "alonw"
TOKEN = "LTSjaeoUn7EVBe6UlmWyxU0UM63lJh7MujBDtm"
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
    MAX_ISSUE_KEY_DIGITS = 5
    if not prefix:
        return []
    jira = get_jira_client()
    split_prefix = prefix.split("-")
    if len(split_prefix) > 1 and split_prefix[0] == "ROAD" and split_prefix[1].isdigit():
        prefix_num = int(split_prefix[1])
        num_to_multiply = len(split_prefix[1])
        or_condition = ""
        multiplier = 1
        for _ in range(num_to_multiply + 1, MAX_ISSUE_KEY_DIGITS):
            multiplier *= 10
            if or_condition != "":
                or_condition += " OR "
            or_condition += (
                f'(issuekey >= "ROAD-{prefix_num*multiplier}" AND issuekey < "ROAD-{(prefix_num + 1)*multiplier}")'
            )
        if or_condition == "":
            return []
        tickets = jira.search_issues(f"({or_condition}) AND project=ROAD ORDER BY issuekey", fields=["summary"])
    else:
        tickets = jira.search_issues(
            f'summary ~ "{prefix}" AND project=ROAD ORDER BY resolution, status, updated DESC', fields=["summary"]
        )
    return tickets


if __name__ == "__main__":
    issue_key = "ROAD-5656"
    image_path = "/homes/dore/Pictures/road3_dml_issue.jpg"
    add_image_in_comment(issue_key, image_path=image_path, comment="updating my task")
    print("Done")

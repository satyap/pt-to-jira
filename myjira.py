import configparser
from tempfile import TemporaryFile

import pt

from jira import JIRA

import people

secrets = configparser.ConfigParser()
secrets.read("secrets.ini")
API_TOKEN = secrets["jira"]["token"]
EMAIL = secrets["jira"]["email"]
jira_url = secrets["jira"]["url"]

board = JIRA(options={"server": jira_url}, basic_auth=(EMAIL, API_TOKEN))
issue_types = board.issue_types()
fields = board.fields()

issue_types_map = {
    "bug": "Bug",
    "chore": "Task",
    "feature": "Epic",
    "story": "Story",
}


def get_issue_type(story):
    s = issue_types_map.get(story["kind"], "Story")
    for t in issue_types:
        if t.name == s and "scope" not in t.raw:  # no scope = global type
            return t.id


def get_field_name(f: str):
    """
    Customer field keys are like custom_field_NNNN which is impenetrable, so map the names to keys.
    :param f:
    :return:
    """
    for t in fields:
        if t["name"] == f:
            return t["key"]


def get_transition(s: str):
    if s == "accepted":
        return "Done"
    if s in ("unstarted", "unscheduled"):
        return "To Do"
    if s in ("delivered", "in progress"):
        return s.capitalize()
    if s == "started":
        return "In Progress"
    raise RuntimeError(f"PT status {s} not known")


def add_issue(project, story):
    issue_fields = {
        "project": project,
        get_field_name("External issue ID"): str(story["id"]),
        "issuetype": {"id": get_issue_type(story)},
        "summary": story["name"].replace("\n", " "),
        "description": desc_with_tasks(story.get("description"), story.get("tasks")),
        get_field_name("created_at"): story["created_at"],
        get_field_name("updated_at"): story["updated_at"],
    }
    reporter = people.user_map.get(story["requested_by_id"])
    if reporter:
        issue_fields["reporter"] = {"id": reporter}
    summary = issue_fields["summary"]
    if len(summary) > 255:
        issue_fields["description"] = f"{summary}\n{issue_fields['description']}"
        issue_fields["summary"] = summary[0:254]
    if story.get("accepted_at"):
        issue_fields[get_field_name("Actual end")] = story["accepted_at"]
    if story.get("labels"):
        issue_fields["labels"] = get_labels(story["labels"])

    issue = find_or_create_issue(project, story, issue_fields)

    board.transition_issue(issue, transition=get_transition(story["current_state"]))
    return issue


def get_labels(pt_labels):
    return [label["name"].replace(" ", "_") for label in pt_labels]


def find_or_create_issue(project, story, issue_fields):
    found_issue = False
    issue = None
    for issue in board.search_issues(f"project={project} and 'External issue ID' = {story['id']}"):
        found_issue = True
    if found_issue:
        issue = board.issue(issue)
        issue.update(issue_fields)
    else:
        issue = board.create_issue(fields=issue_fields)
    print(f'{story["id"]}: {issue}')
    return issue


def update_comments(issue, comment):
    existing_comments = board.comments(issue)
    by = people.names[str(comment["person_id"])]
    blurb = f"{comment['id']} \nBy {by}\ncreated: {comment['created_at']}\nupdated: {comment.get('updated_at')}"
    text = f"{blurb}\n\n{comment.get('text')}"
    if comment.get("file_attachments"):
        add_attachments(issue, comment)
        text += f"\nAttachment(s): {'; '.join([a.get('filename') for a in comment['file_attachments']])}"
    if not update_existing_comment(comment["id"], text, existing_comments):
        board.add_comment(issue, text)


def update_existing_comment(comment_id, pt_comment, existing_comments):
    """Find and update an existing comment; return true, if not found return false"""
    starter = f"{comment_id} "
    for existing in existing_comments:
        if existing.body.startswith(starter):
            existing.update(body=pt_comment)
            return True
    return False


def add_attachments(issue, comment):
    existing_attachments = [attachment.filename for attachment in issue.fields.attachment]
    for attachment in comment["file_attachments"]:
        if attachment["filename"] in existing_attachments:
            continue
        with TemporaryFile() as tf:
            pt.get_attachment(attachment, tf)
            board.add_attachment(issue, attachment=tf, filename=attachment["filename"])


def desc_with_tasks(desc, tasks):
    if not tasks:
        return desc
    if not desc:
        desc = ""
    for task in tasks:
        if task and task.get("description"):
            desc += f"\nTask: {'(done) ' if task['complete'] else ''}{task['description']}"
    return desc


def get_people():
    for u, p in board.group_members(secrets["jira"]["group"]).items():
        print(u, board.user(u))

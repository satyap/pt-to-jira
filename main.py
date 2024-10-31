import sys

import myjira
import pt

jira_project = "ABCD"
pt_project_id = 1234567


def migrate_story(story):
    print(f'{story["id"]} ...')
    issue = myjira.add_issue(jira_project, story)
    num_comments = 0
    for comment in pt.comments(pt_project_id, story):
        myjira.update_comments(issue, comment)
        num_comments += 1
    print(f'{story["id"]}: {num_comments} comment(s)')


start_offset = sys.argv[1] if len(sys.argv) > 1 else 0
print(f"Starting at offset {start_offset}")
for story in pt.stories(pt_project_id, start_offset):
    migrate_story(story)

import myjira
import pt

# Just map PT user ids to jira user ids, since jira makes it so hard to map via email.
user_map = {
        "1234568": "12456:aaaa-bbbb-cccc",
}

# Also map PT IDs to names so we can add them in comments.
names = {
    "1234568": "My Name",
}


def get(account_id):
    print(myjira.get_people())

    for p in pt.get(f"/accounts/{account_id}/memberships").json():
        print(f'"{p["id"]}": "{p["person"]["email"]}", ')

if __name__ == '__main__':
    pt_account_id = 123456
    get(pt_account_id)

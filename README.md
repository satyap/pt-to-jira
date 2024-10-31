# Pivotal Tracker to Jira converter

Converts Pivotal Tracker stories into Jira tickets using their APIs.

Does not write anything to Pivotal Tracker. Makes new stories in Jira.

## Must have!!

It is _very strongly recommended_ to use a test project on the Jira side. You can move the tickets later.

## Required

* Ability to read Python and write at least a little Python.
* Jira API key with sufficient permissions. Admin is recommended.
* Pivotal Tracker API key with sufficient permissions.

### Read the code

Make sure this does what you need! There's not that much code here.

## Configuration

Copy `secrets.ini.example` to `secrets.ini` and fill in the relevant details.
It is _very strongly recommended_ to use a test project on the Jira side.

You will need to put the appropriate ID in `people.py` as well, near the bottom of the file.

## Setup

Create a Python virtual environment and run `pip install -r requirements.txt`.

In Jira add a field for "External issue ID" so that the PT story ID can be stored, and thus the script can find what it has done before.

## Get the people

Run `people.py` and put the relevant information that gets printed into the maps at the top of `people.py`.

## Run the script

Run `python main.py`.

This takes a while, so you can always stop it and then re-run it with a new offset. Suppose it
had gotten as far as story TEST-800. You can run `main.py 750` and it'll do the
last 50 stories again, and continue from there. That assumes you did this with
a fresh test project _as recommended_, and so you really did have 800 stories
done so far.

## What does it do?

The first run of `people.py` is for mapping your PT users to Jira user IDs.

The main run, of `main.py`, lists all the PT stories in a paginated way. It uses the external issue id field in Jira to find any ticket it had already created.

It sets the story's reporter, summary, description fields. It adds PT labels as needed.

Comments get copied over, however all comments will be attributed to the user
running the script. Each comment will include the original commenter's name as
set in the 2nd map in `people.py`. It will also include the original
timestamps.

Attachments from PT will get copied over. Attachments in Google Drive will _not_.
PT attachments are associated with a comment. In Jira, all attachments go on the story. There will be a comment telling you the file _name_. It's not perfect but it gets the job done.

Story tasks from PT will be added to the Jira ticket description. There will be
a text of `(done)` if the task was marked completed.


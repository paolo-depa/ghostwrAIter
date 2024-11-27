import argparse
import datetime
import json
import os
import requests
import sys
from bugzilla import Bugzilla


# Define attributes globally
BZ_OPT_ATTRS = [
    'reporter', 'creator', 'assigned_to', 'keywords', 'op_sys', 
    'platform', 'component', 'version', 'product', 'is_open', 
    'status', 'whiteboard'
]

class JsonBug:

    def __init__(self, bug, comments=None):
        """
        Initialize a JsonBug instance.

        Args:
            bug (Bug): The Bugzilla bug object.
            comments (list, optional): A list of comments associated with the bug. Defaults to None.
        """
        if not hasattr(bug, 'id'):
            raise ValueError("Error: Bug ID is mandatory.")
        self.bug_id = bug.id
        self.comments = comments if comments is not None else []
        
        # List of non-mandatory attributes
        for attr in BZ_OPT_ATTRS:
            setattr(self, attr, getattr(bug, attr, None))

    def to_json(self):
        """
        Convert the JsonBug instance to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary containing the bug ID, comments, and other attributes.
        """
        json_data = {'bug_id': self.bug_id, 'comments': self.comments}
        
    def __init__(self, comment):
        """
        Initialize a JsonComment instance.

        Args:
            comment (dict): A dictionary containing comment details such as id, text, creator, creation_time, is_private, and optionally attachment_id.
        """
            json_data[attr] = getattr(self, attr, '')
        
        return json_data

class JsonComment:
    
    def __init__(self, comment):
        self.id = comment['id']

        # List of non-mandatory attributes
        self.text = comment['text']
        self.creator = comment['creator']
        # Extract the first 19 characters for 'YYYY-MM-DD HH:MM:SS' format
        self.creation_time = str(comment['creation_time'])[0:19]
        self.is_private = comment['is_private']
        if comment.get('attachment_id'):
            self.attachment_id = comment['attachment_id']

    def to_json(self):
        json_data = {
            'id': self.id,
            'text': self.text,
            'creator': self.creator,
            'creation_time': self.creation_time,
            'is_private': self.is_private,
        }
        if hasattr(self, 'attachment_id'):
            json_data['attachment_id'] = self.attachment_id

        return json_data

# Load environment variables from bugzilla-scraper.json
env_file = os.path.join(os.path.dirname(__file__), 'bugzilla-scraper.json')
if not os.path.exists(env_file):
    if os.path.exists(os.path.expanduser('~/.config/ghostwraiter/bugzilla-scraper.json')):
      env_file = os.path.expanduser('~/.config/ghostwraiter/bugzilla-scraper.json')
    else:
      print("Error: Configuration file not found.")
      sys.exit(1)

config = {}
if os.path.exists(env_file):
    with open(env_file) as f:
        config = json.load(f)

    if 'url' not in config:
        print("Error: Bugzilla URL not found in configuration file.")
        sys.exit(1)
    if 'api_key' not in config:
        print("Error: Bugzilla api_key not found in configuration file.")
        sys.exit(1)
else:
    print("Error: Configuration file not found.")
    sys.exit(1)
parser = argparse.ArgumentParser(description='A script to scrape and retrieve bug information from a Bugzilla instance.')
parser.add_argument('--id', type=int, help='Bug ID')
for attr in BZ_OPT_ATTRS:
    parser.add_argument(f'--{attr}', type=str, help=f'{attr.capitalize()}')

args = parser.parse_args()

# Initialize Bugzilla connection
bugzilla_url = config['url']
api_key = config['api_key']
try:
    bz = Bugzilla(url=bugzilla_url, api_key=api_key)
except requests.exceptions.ConnectionError as e:
    print(f"Error: Unable to connect to Bugzilla: {e}")
    sys.exit(1)
except requests.exceptions.HTTPError as e:
    print(f"Error: HTTP error occurred: {e}")
    sys.exit(1)
except requests.exceptions.InvalidURL as e:
    print(f"Error: Invalid URL: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: An unexpected error occurred: {e}")
    sys.exit(1)

# Build query parameters
query_params = {}
# Set default query parameters from config file if available
if 'query' in config:
    query_params.update(config['query'])

if args.id:
    query_params['id'] = args.id

for attr in BZ_OPT_ATTRS:
    arg_value = getattr(args, attr, None)
    if arg_value is not None:
        query_params[attr] = arg_value

# Check if query parameters are empty
if not query_params:
    print("Error: No query parameters provided.")
    sys.exit(1)

# Query Bugzilla
try:
    print(f"-- Querying Bugzilla with parameters: {query_params}")
    bugs = bz.query(query_params)
    print(f"-- Retrieved {len(bugs)} bugs.")
except Exception as e:
    print(f"Error: Unable to query Bugzilla: {e}")
    sys.exit(1)

jsonbugs = []
bug_ids = [bug.id for bug in bugs]
try:
    # Retrieve comments for each bug: API allows to do it in one call
    # a list of bug ids is passed to the get_comments method
    # the call returns a dictionary with the bug ids as keys and the comments as values
    resultset = bz.get_comments(bug_ids)

    for bugid in resultset['bugs']:
        jsoncomments = []
        
        # Retrieve the corresponding bug from the original list where it is fully populated
        bug = next((b for b in bugs if b.id == int(bugid)), None)

         # jsonize its comments
        comments = resultset['bugs'].get(bugid)
        print(f"-- Retrieved {len(comments)} comments for bug {bug.id}. --")
        if comments['comments']:
           for comment in comments['comments']:
                jsoncomments.append(JsonComment(comment).to_json())
        
        jsonbugs.append(JsonBug(bug=bug, comments=jsoncomments).to_json())
except Exception as e:
    print(f"Error: Unable to retrieve comments: {e}")
    sys.exit(1)

print(json.dumps(jsonbugs, indent=4) + '\n')

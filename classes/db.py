from flask import g
from pyairtable import Base
import os

# method to add the db instance to the request context
def get_db():
    if 'db' not in g:
        # if production mode
        if(os.environ.get("AIRTABLE_API_KEY") != None and os.environ.get("AIRTABLE_BASE_ID") != None ):
            AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
            AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
        # if development mode
        else:
            # airtable apy key to consume RESTapis
            AIRTABLE_API_KEY = "keycsjEIxJKGt7nKj"
            # airtable base id
            AIRTABLE_BASE_ID = "apppcwpHIxEYOTzbE"
            
        # create airtable istance
        base = Base(AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
        
        # add airtable instance to request context
        g.db = base
    return g.db


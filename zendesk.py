"""Zendesk Utilities

Usage:
  zendesk.py tag_users <tag> <path_to_email_list>
  
"""

from os import getenv

import requests
from docopt import docopt
from tqdm import *

ZENDESK_BASE = 'https://waveaccounting2.zendesk.com'
#ZENDESK_USERNAME = getenv('ZD_USERNAME')
#ZENDESK_TOKEN = getenv('ZD_TOKEN')
ZENDESK_USERNAME = 'rhamilton@waveaccounting.com'
ZENDESK_TOKEN = ''

if not all([ZENDESK_TOKEN, ZENDESK_USERNAME]):
	raise Exception("Did you forget to set ZD_USERNAME and/or ZD_TOKEN variables?")

if '/token' not in ZENDESK_USERNAME:
	ZENDESK_USERNAME += '/token'

ZENDESK_AUTH = (ZENDESK_USERNAME, ZENDESK_TOKEN)

def bulk_tag(tag_name, identifiers, obj_name):
	num_tagged = 0
	print " Tagging {} things".format(len(identifiers))
	
	for zd_id in tqdm(identifiers):
		url = ZENDESK_BASE + '/api/v2/{obj_name}/{zd_id}/tags.json'.format(zd_id=zd_id, obj_name=obj_name)
		tag_params = {
			'tags': [tag_name],
		}
		
		resp = requests.put(url, json=tag_params, auth=ZENDESK_AUTH)
		
		if resp.status_code == 200:
			num_tagged += 1
		else:
			print "Error - got a {err} when tagging {zd_id}".format(err=resp.status_code, zd_id=zd_id)
			
	return num_tagged
	
def parse_file_into_list(filename):
	with open(filename, 'r') as f:
		lines = f.readlines()
	return [l.strip() for l in lines]

def get_or_create_users(user_emails):
	zd_ids = []
	num_existing, num_created = 0, 0
	
	print ">> Finding {} users".format(len(user_emails))
	
	for email in tqdm(user_emails):
		zd_id = _get_user_id_from_email(email)
		if zd_id:
			zd_ids.append(zd_id)
			num_existing += 1
		else:
			zd_ids.append(_create_user_from_email(email))
			num_created += 1
			
	return zd_ids, num_existing, num_created
	
def _get_user_id_from_email(email):
	"""None if no user exists by that email, their Zendesk ID otherwise"""
	
	resp = requests.get(ZENDESK_BASE + "/api/v2/users/search.json?query={email}".format(email=email), auth=ZENDESK_AUTH).json()
	
	if resp['count'] == 0:
		return None
	elif resp['count'] == 1:
		return resp['users'][0]['id']
	else:
		raise Exception("{num} users found for email {email}".format(num=resp['count'], email=email))
	
def _create_user_from_email(email):
	user_params = {
		'user': {
			'role': 'end-user',
			'name': email.split('@', 1)[0],
			'email': email,
		}
	}
	
	resp = requests.post(ZENDESK_BASE + "/api/v2/users.json", json=user_params, auth=ZENDESK_AUTH)
	
	if resp.status_code == 201:
		return resp.json()['user']['id']
	else:
		raise Exception("Got a {code} when trying to create {email}".format(code=resp.code, email=email))


if __name__ == '__main__':
	arguments = docopt(__doc__, version='Zendesk Utilities 0.0.1')
	
	if arguments['tag_users']:
		user_emails = parse_file_into_list(arguments['<path_to_email_list>'])
		user_ids, num_existing, num_created = get_or_create_users(user_emails)
		num_tagged = bulk_tag(arguments['<tag>'], user_ids, 'users')
		
		print "{} users tagged ({} users created in the process)".format(num_tagged, num_created)

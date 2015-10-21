# Copyright (c) 2015 Sergiusz 'q3k' Bazanski <serigusz@bazanski.pl>
# This is free and unencumbered software released into the public domain.
__author__ = "Sergiusz 'q3k' Bazanski"

import hashlib
import json
import time

import MySQLdb
import requests

REFRESH_TIME = 30
OUTPUT_REPORT = 'at.json'
LEASE_URL = 'http://10.0.10.5/dhcp.leases'
LEASE_CACHE_TIMEOUT = 10  # seconds
MYSQL_USER = 'root'
MYSQL_DB = 'members'

lease_cache_time = 0
lease_cache_data = []
def get_leases():
    """Download and cache leases from router."""
    global lease_cache_time, lease_cache_data

    # Check cache
    now = time.time()
    if now < lease_cache_time + LEASE_CACHE_TIMEOUT:
        return lease_cache_data

    # Get leases
    text = requests.get(LEASE_URL).text
    macs = []
    for line in text.split('\n'):
        if not line.strip():
            continue
        mac = line.split()[1]
        macs.append(mac)

    # Update cache
    lease_cache_data = macs
    lease_cache_time = now
    return macs


def _connect_db():
    """Connect to MySQL user database and return a cursor."""
    db = MySQLdb.connect(user=MYSQL_USER, db=MYSQL_DB)
    return db.cursor()


def _anonymyze_email(email):
    """Anonymize an email to make spiders piss off."""
    # For now we change the last character of the user part and first domain
    # part to a '?'. Good enough?
    user_part, domains_part = email.split('@')
    first_domain = domains_part.split('.')[0]
    rest_domains = '.'.join(domains_part.split('.')[1:])

    user_part = user_part[:-1] + '?'
    first_domain = first_domain[:-1] + '?'

    return '{}@{}.{}'.format(user_part, first_domain, rest_domains)


def _hash_mac(mac, salt):
    h = hashlib.sha1()
    h.update(salt)
    h.update(mac)
    return h.hexdigest()


def get_clients(macs):
    """Transform a list of macs into a client->macs name dictionary."""
    SALT = 'salT'  # hack! this might not always be the real salt.
    hashed_macs = dict((_hash_mac(m, SALT), m) for m in macs)
    sql_macs = ', '.join('"{}"'.format(m) for m in hashed_macs)

    cursor = _connect_db()
    cursor.execute('SELECT email, mac FROM Users WHERE mac IN (' + sql_macs + ')')

    clients = {}
    for email, hashed_mac in cursor.fetchall():
        mac = hashed_macs[hashed_mac]
        if email not in clients:
            clients[email] = []
        clients[email].append(mac)
    return clients


def generate_json():
    macs = get_leases()
    clients = get_clients(macs)
    return json.dumps([_anonymyze_email(e) for e in clients.keys()])


# If we are being run as a library, start the main loop
if __name__ == '__main__':
    while True:
        try:
            j = generate_json()
        except Exception as e:  # gotta catch 'em all :^)
            print 'Exception: ' + str(e)
        with open(OUTPUT_REPORT, 'w') as f:
            f.write(j)
        time.sleep(REFRESH_TIME)

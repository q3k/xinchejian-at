XinCheJian Checkinator
======================

Inspired by https://at.hackerspace.pl/, hacked together in 30 minutes by q3k.

Setup
-----

Install python, python-requests, python-mysqldb.

Usage
-----

Just run at.py. It will download a leasefile from the router and output an at.json at perpetuum. Serve this with a static file server or push it somewhere.

If you want the script to scp the resulting report for you, run it with the destination scp string as its' argument, ie. `python2 at.py torvalds@example.com:/var/www/examples.com/`.

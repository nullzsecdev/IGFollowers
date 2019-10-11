#!/usr/bin/env python3

import argparse
import instaloader
import texttable as tt
import os

USERNAME=None
PASSWORD=None
mod_path = os.path.dirname(os.path.realpath(__file__))
try:
    with open(f"{mod_path}/instagram_creds", 'r') as f:
        creds = f.readline()
        user,password = creds.split(':')
        if user != 'username' and password != 'password':
            USERNAME = user.strip()
            PASSWORD = password.strip()
except:
    pass


parser = argparse.ArgumentParser(description="""
        igfollowers is a tool for performing basic actions on an instagram account(s) followers.
        
        NOTE: This tool requires valid instagram credentials to work. You can either pass them as arguments (-u, -p), write them to the file 'instagram_creds in the repository's root directory, or hardcode them into the igfollowers.py file (NOT RECOMMENDED).
        """)
parser.add_argument('--only-mutual', action="store_true", help="Limit the results to only users who follow ALL profiles scanned.")
parser.add_argument('-u', '--username', type=str, help="Instagram username to login with.")
parser.add_argument('-p', '--password', type=str, help="Instagram password to login with.")
parser.add_argument('profiles', nargs="+", metavar="profile", help="The username of the instagram profile you want to get the followers for.")

args = parser.parse_args()
USERNAME = args.username if args.username is not None else USERNAME
PASSWORD = args.password if args.password is not None else PASSWORD
if USERNAME is None or PASSWORD is None:
    print("A username and password must be specified or hardcoded.")
    parser.print_help()

def print_profiles(profiles):
    tab = tt.Texttable()
    tab.header(['User Id', 'Full Name', 'Username', 'Profile URL'])
    tab.set_deco(tt.Texttable.HEADER)
    # tab.set_cols_width([10, 30, 25, 45])
    tab.set_max_width(0)
    tab.set_cols_dtype(['i', 't', 't', 't']) # automatic
    for profile in profiles:
        tab.add_row((profile.userid, profile.full_name, profile.username, f"http://instagram.com/{profile.username}/"))
        # print(f"{profile.full_name} ({profile.username})[http://instagram.com/{profile.username}/]")
    s = tab.draw()
    print(s)
    print("\n\n")

loader = instaloader.Instaloader()
loader.login(USERNAME,str(PASSWORD))

profiles = []
print("Loading profiles...")
for profile in args.profiles:
    print(f"Loading profile: {profile}")
    prof = instaloader.Profile.from_username(loader.context, profile)
    profiles.append(prof)


followers_by_profile = {}
print("Loading followers for each profile...")
for profile in profiles:
    followers = set(profile.get_followers())
    followers_by_profile[profile.username] = followers
    

if args.only_mutual:
    print("Filtering followers...")
    all_sets = list(followers_by_profile.values())
    first = all_sets.pop()
    mutual = first
    if len(all_sets) > 0:
        mutual = first.intersection(*all_sets)
    print("\nMutual Followers:")
    print_profiles(mutual)

else:
    for user in followers_by_profile.keys():
        print(f"\n{user}'s 'Followers:")
        profiles = followers_by_profile[user]
        print_profiles(profiles)




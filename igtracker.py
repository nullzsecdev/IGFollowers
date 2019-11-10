#!/usr/bin/env python3

import argparse
import instaloader
import texttable as tt
import os, sys
import lzma
from pprint import pprint
from typing import Any, Dict, Iterator, List, Optional, Union
import IPython
from crontab import CronTab
import datetime
import arrow
import re
from prompt_toolkit import prompt
# import PyInquirer
import operator

USERNAME=None
PASSWORD=None
parser = argparse.ArgumentParser(description="""
            igtracker is a tool for tracking certain metrics of a profile.
            
            NOTE: This tool requires valid instagram credentials to work. You can either pass them as arguments (-u, -p), write them to the file 'instagram_creds in the repository's root directory, or hardcode them into the igtracker.py file (NOT RECOMMENDED).
            """)


mod_path = os.path.dirname(os.path.realpath(__file__))
profiles = []

def post_repr(self: instaloader.Post):
    r = f"""
    <Post
    id: {self.mediaid}
    date: {self.date_utc}
    content: {self.url}
    caption: {self.caption}
    type: {self.typename}
    location: {self.location}> 
    """
    return r
instaloader.Post.__repr__ = post_repr


class PostQuery:

    def __init__(self):
        self.params = []
    
    def set_interactive(self, after_date=None, before_date=None, caption_filter=None):
        print("Filter posts:")
        if after_date is None and before_date is None and caption_filter is None:
            after_date = prompt("after date (format: YYYY-mm-dd [hh:mm:ss]) default: [1970-01-01 00:00:00]: ")
            before_date = prompt("before date (format: YYYY-mm-dd [hh:mm:ss]) default: [now]: ")
            caption_filter = prompt("where caption matches regex default: [none]: ")

        if after_date is not None and after_date != "":
            self.add_date("date", operator.gt, arrow.get(after_date))
        if before_date is not None and before_date != "":
            self.add_date("date", operator.lt, arrow.get(before_date))
        if caption_filter is not None and caption_filter != "":
            self.add_regex("caption", caption_filter)

    # def delete_interactive(self):
    #     options = list(map(lambda param: param[2], self.params)
    #     options.append("back")
    #     picked, index = pick(options, "Which condition do you want to remove?")
    #     if picked == "back":
    #         return
    #     else:
    #         del self.params[index]
    
    # def print_params(self):
    #     print("Active Filters\n-------------")
    #     for param in self.params:
    #         print(param[2])

    def add_regex(self, field, expression):
        matcher = re.compile(expression)
        self.add_param(
            field, 
            lambda val: matcher.match(val),
            f"{field} matches {expression}"
            )
        

    def add_date(self, field, operator, compare_to):
        self.add_param(
            field,
            lambda val: operator(arrow.get(val), compare_to),
            f"{field} {operator} {compare_to}"
            )
    def add_numeric(self, field, operator, compare_to):
        self.add_param(
            field,
            lambda val: operator(val, compare_to),
            f"{field} {operator.__qualname__} {compare_to}"
            )

    def add_param(self, field, checker, string_rep=""):
        self.params.append((field, checker))

    def check_post(self, post):
        checks = map(lambda param: param[1](getattr(post, param[0])), self.params)
        return all(checks)


    def filter_posts(self, posts):
        posts = filter(
            lambda post: self.check_post(post),
            posts
        )
        return list(posts)




class Profile(instaloader.Profile):

    def __init__(self, context:instaloader.InstaloaderContext, node: Dict[str, any]):
        self._posts = []
        super().__init__(context, node)

    @property
    def post_count(self):
        count = self._metadata('edge_owner_to_timeline_media')['count']
        count = int(count)
        return count
        
    @property
    def dictval(self):
        return self._asdict()

    @property
    def posts(self):
        if len(self._posts) < self.post_count:
            print("Using fetched posts")
            return list(self.get_posts())
        else:
            print("Using stored posts")
            return self._posts

    def get_posts(self) -> Iterator[instaloader.Post]:
        for post in super().get_posts():
            if post not in self._posts:
                self._posts.append(post)
            yield post

    def show_metrics(self):
        last_post = self.posts[0].date
        print(last_post)
    
    def filter_posts(self, query: PostQuery):
        pass

    def search_posts(self, after=None, before=None, caption=None):
        query = PostQuery()
        query.set_interactive(after, before, caption)

        return query.filter_posts(self.posts)

    def log_posts(self):
        log_file = f"{args.data_location}logs/{self.username}.log"
        if os.path.exists(log_file):
            last_write = os.path.getmtime(log_file)
            posts = self.search_posts(after=last_write)
        else: 
            posts = self.posts
       
        print(f"Logging {len(posts)} posts")
        with open(log_file, 'a') as f:
            for post in posts:
                f.write(repr(post))

def post_log_entry(post, format):
    pass
        
def get_all_profiles(path):

    dirs = os.listdir(path)
    return dirs

def make_data_dir(data_dir):
    try:
        os.makedirs(data_dir)
    except:
        print(f"Couldn't create data directory {data_dir}. Either make it yourself, and ensure your user has write access in it. Or change the path to a writable location with --data-location.")
        sys.exit(1)

def check_data_dir(data_dir):
    try:
        if not os.path.exists(data_dir):
            make_data_dir(data_dir)
        if not os.path.exists( f"{data_dir}profiles/"):
            make_data_dir(f"{data_dir}profiles/")
        if not os.path.exists( f"{data_dir}logs/"):
            make_data_dir(f"{data_dir}logs/")
    except:
        print("There was an error creating the data dir. Please check the path specified in --data-location and try again.")
        sys.exit(1)

def init_loader(data_location):
    global loader
    if data_location[:-1] != "/":
        data_location += "/"
    data_location += "profiles/{target}"
    loader = instaloader.Instaloader(dirname_pattern=data_location)

def login(username, password):
    if username is None:
        try:
            with open(f"{mod_path}/instagram_creds", 'r') as f:
                creds = f.readline()
                user,password = creds.split(':')
                if user != 'username' and password != 'password':
                    username = user.strip()
                    password = password.strip()
        except:
            print("A username and password must be specified or hardcoded.")
            parser.print_help()
    if password is None:
        password = str(input(f"Password for {username}: "))

    loader.login(username,password)

def get_args():
    global args, parser
    parser.add_argument('--log', action="store_true", help="Write results to the logfile.")
    parser.add_argument('--slow', dest="fast_update", action="store_false", help="Dont stop when getting to already downloaded post.")
    parser.add_argument('--init-logservice', action="store_true", help="Run this to create the logservice. Use -f to set the frequency to check for new posts. The rest of the arguments will remain the same when it gets run.")
    parser.add_argument('-f', '--frequency', type=int, default=10, help="Frequency (in minutes) to run the script.")
    parser.add_argument('--format', type=str, default="id: {id}\ncontent: {display_url}\ncaption: {}", help="Frequency (in minutes) to run the script.")
    parser.add_argument('-d', '--data-location', default="/var/igtracker/", help="The location to store the downloaded profile data.")
    parser.add_argument('--interactive', action="store_true", help="Drop into an interactive shell to query the profile after update is performed. Use --no-update to skip downloading new profile info.")
    parser.add_argument('--no-update', action="store_false", dest='update', help="Skip downloading new profile info.")
    parser.add_argument('--stats', action="store_true", dest='show_stats', help="Show statistics for each profile.")
    parser.add_argument('-u', '--username', default=USERNAME, type=str, help="Instagram username to login with.")
    parser.add_argument('-p', '--password', default=PASSWORD, type=str, help="Instagram password to login with.")
    parser.add_argument('profiles', nargs="*", metavar="profile", help="The username of the instagram profile you want to track. If no profile specified it will default to all profiles in DATA_LOCATION")

    args = parser.parse_args()


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

def aggregate(fast_update=True):
    loader.download_profiles(profiles, fast_update=fast_update)

def show_stats():
    for profile in profiles:
        profile.show_metrics()

def load_profiles(usernames):
    global profiles
    if len(usernames) == 0:
        path = args.data_location
        usernames = get_all_profiles(f"{path}profiles/")
    print("Loading profiles...")
    for profile in usernames:
        print(f"Loading profile: {profile}")
        prof = Profile.from_username(loader.context, profile)
        profiles.append(prof)

def show_posts(profile):
    for post in profile.get_posts():
        pprint(post)

def list_profiles():
    print(list(map(lambda x: x.username, profiles)))

def show(username):
    print("TODO: Implement better repr of profile")
    profile = next(prof for prof in profiles if prof.username == username)
    if profile is not None:
        pprint(profile.dictval)
    else:
        print("Coulnd't find that profile")


def interactive():
    header = """
    This is an interactive python shell.
    
    You can access the loaded profiles through the profiles variable.
    Use list_profiles() to show the available profiles.
    Use show([username]) to show the profile for a username.

    To see what methods and properties are available on an object use: dir([object])

    You can interact with a specific profile like this:
    In [1]: p = profiles[0]                                                                                                                                                                                                       

    In [2]: p.followers                                                                                                                                                                                                           
    Out[2]: 92

    In [3]: p.followees                                                                                                                                                                                                           
    Out[3]: 134

    In [4]: p.posts                                                                                                                                                                                                           
    Out[4]: 
    [<Post BHiAH12ARwz>,
    <Post 7f8JSAx9uM>]

    In [5]: filtered_posts = p.search_posts(after="2019-01-01", caption=".*friends.*")                                                                                                                                                                                                           
    Out[5]: [<Post BHiAH12ARwz>]

    """
    IPython.embed(header=header)


def set_crontab(frequency, format):
    usernames = list(map(lambda prof: prof.username, profiles))
    username_list = " ".join(usernames)
    job_command = f"{mod_path} --log --format {format} {username_list}"
    user = os.getlogin()
    cron = CronTab(user=user)
    job = None
    for cronjob in cron:
        if cronjob.comment == "IG Log":
            job = cronjob
    if job is None:
        job = cron.new(command=job_command, comment="IG Log")
    else:
        job.command = job_command
    job.every(frequency)

    cron.write()
    


if __name__ == "__main__":
    get_args()
    check_data_dir(args.data_location)
    init_loader(args.data_location)
    login(args.username, args.password)
    load_profiles(args.profiles)
    if args.update:
        aggregate(args.fast_update)
    if args.show_stats:
        show_stats()
    if args.init_logservice:
        set_crontab(args.frequency, args.format)
    if args.log:
        for profile in profiles:
            profile.log_posts()
    if args.interactive:
        interactive()


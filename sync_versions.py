#!/usr/bin/env python3
import docker
import argparse
import requests
import re
import json

def main():
    """cli entrypoint"""
    parser = argparse.ArgumentParser(description="Cleanup docker registry")
    parser.add_argument("-e", "--exclude",
                        dest="exclude",
                        help="Regexp to exclude tags")
    parser.add_argument("-E", "--include",
                        dest="include",
                        help="Regexp to include tags")
    parser.add_argument("-i", "--image",
                        dest="image",
                        required=True,
                        help="Docker image to cleanup")
    parser.add_argument("-v", "--verbose",
                        dest="verbose",
                        action="store_true",
                        help="verbose")
    parser.add_argument("-u", "--registry-url",
                        dest="registry_url",
                        default="http://localhost",
                        help="Registry URL")
    parser.add_argument("-l", "--last",
                        dest="last",
                        default=5,
                        type=int,
                        help="Keep last N tags")
    parser.add_argument("-U", "--user",
                        dest="user",
                        help="User for auth")
    parser.add_argument("-P", "--password",
                        dest="password",
                        help="Password for auth")
    parser.add_argument("--no_check_certificate",
			action='store_false')
    args = parser.parse_args()

    try:
        client = docker.from_env()
        online = client.info()
        if (args.verbose):
            print ("local docker client info")
            print (json.dumps(online, sort_keys=True, indent=4))
            print ("#########################")

    except docker.errors.APIError as e:
        print (e)

    # Get catalog
    if args.user and args.password:
        auth = (args.user, args.password)
    else:
        auth = None
    try:    
        response = requests.get(args.registry_url + "/v2/_catalog?n=1000",
                            auth=auth, verify=args.no_check_certificate)
        repositories = response.json()["repositories"]
        if (args.verbose):
            print ("Repositories list:")
            print (json.dumps(repositories, sort_keys=True, indent=4))
            print ("#########################")
    except: 
        print ("could nod read the remote repositories")
    # For each repository check it matches with args.image
    for repository in repositories:
        if re.search(args.image, repository):
       
            # Get tags
          try: 
            response = requests.get(args.registry_url + "/v2/" + repository + "/tags/list",
                                    auth=auth, verify=args.no_check_certificate)
            tags = response.json()["tags"]
            if (args.verbose):
                print (json.dumps(tags, sort_keys=False, indent=4))
             # For each tag, check it does not matches with args.exclude
            matching_tags = []
            for tag in tags:
         
                if not args.exclude or not re.search(args.exclude, tag):
                    if not args.include or re.search(args.include, tag):
                        matching_tags.append(tag)

            # Sort tags
            matching_tags.sort(key=lambda s: LooseVersion(re.sub('[^0-9.]', '9', s)))
          except:
            print ("tags could not be fetched") 

            # Delete all except N last items
            if args.last > 0:
                tags_to_delete = matching_tags[:-args.last]
            else:
                tags_to_delete = matching_tags
            for tag in tags_to_delete:
                
                print(json.dumps(tags_to_delete, sort_keys=False, indent=4))    


if __name__ == '__main__':
    main()
    
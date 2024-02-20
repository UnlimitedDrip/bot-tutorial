import os
from flask import Flask, request
from github import Github, GithubIntegration
from datetime import datetime, timedelta

app = Flask(__name__)

app_id = '821462'

# Read the bot certificate
with open(
        os.path.normpath(os.path.expanduser('aaron-sossbot.2024-02-07.private-key.pem')),
        'r'
) as cert_file:
    app_key = cert_file.read()
    
# Create an GitHub integration instance
git_integration = GithubIntegration(
    app_id,
    app_key,
)

def pr_opened_event(repo, payload):
    pr = repo.get_issue(number=payload['pull_request']['number'])
    author = pr.user.login

    is_first_pr = repo.get_issues(creator=author).totalCount

    if is_first_pr == 1:
        response = f"Thanks for opening this pull request, @{author}! " \
                   f"The repository maintainers will look into it ASAP! :speech_balloon:"
        pr.create_comment(f"{response}")
        pr.add_to_labels("needs review")

    elif streak_checker(repo):
        response = f"Thanks for opening this pull request, @{author}! " \
                   f"The repository maintainers will look into it ASAP! :speech_balloon:"\
        f"Congrats, @{author}! You have maintained your daily streak!"
        pr.create_comment(f"{response}")
        pr.add_to_labels("needs review")

    else:
        response = f"Thanks for opening this pull request, @{author}! " \
                   f"The repository maintainers will look into it ASAP! :speech_balloon:"\
        f"Hey, @{author}! Unfortunately, you have not maintained your daily streak!"
        pr.create_comment(f"{response}")
        pr.add_to_labels("needs review")


#streak
def streak_checker(repo):
    commits = repo.get_commits()
    last_commit = commits[0]

    commit_time = last_commit.commit.author.date

    time = datetime.utcnow() - commit_time

    return time < timedelta(hours=24)
    
#user stats
def user_stats(username, git_connection):
    contributions = git_connection.get_user(username).public_repos

    return f"@{username}'s public repos: {contributions}"

@app.route("/", methods=['GET','POST'])
def bot():
    payload = request.json

    #testing
    print("Payload: ", payload)

    if not 'repository' in payload.keys():
        return "", 204

    owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']

    git_connection = Github(
        login_or_token=git_integration.get_access_token(
            git_integration.get_installation(owner, repo_name).id
        ).token
    )
    repo = git_connection.get_repo(f"{owner}/{repo_name}")

    # Check if the event is a GitHub pull request creation event
    if all(k in payload.keys() for k in ['action', 'pull_request']) and payload['action'] == 'opened':
        pr_opened_event(repo, payload)

    
    #check if comment has STATS in it
    if 'comment' in payload.keys() and 'body' in payload['comment'] and 'STATS' in payload['comment']['body']:
        username = payload['comment']['user']['login']
        stats_response = user_stats(username, git_connection)
        repo.get_issue(number=payload['issue']['number']).create_comment(stats_response)

    return "", 204

if __name__ == "__main__":
    app.run(debug=True, port=5000)

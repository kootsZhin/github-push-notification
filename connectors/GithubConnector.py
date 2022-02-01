from datetime import datetime as dt
from datetime import timedelta as td

import requests
import settings


class GithubConnector:
    def __init__(self, language, searchRange, pingRange):
        self.base_url = settings.GITHUB_BASE_URL
        self.language = language
        self.searchRange = searchRange
        self.pingRange = pingRange

    def getLatestRepositories(self, language, searchRange, pingRange):
        """
        getLatestRepositories() gets the latest updates from Github API using the input query parameters

        :language: string, target language
        :searchRange: number, range while querying through Github API, min 1 day (unit: days)
        :pingRange: number, range while querying through Github API, min 1 day (unit: days)
        """
        updates = []

        timeNow = dt.utcnow()
        timeBefore = dt.utcnow() - td(days=searchRange)

        formattedTime = timeNow.strftime('%Y-%m-%d')
        formattedTimeBefore = timeBefore.strftime('%Y-%m-%d')

        queryString = f"pushed:{formattedTimeBefore}..{formattedTime} language:{language}"
        querySort = "updated"
        print(queryString)

        queryResponse = requests.get(self.base_url + "/search/repositories", params={
            "accept": "application/vnd.github.v3+json",
            "q": queryString,
            "sort": querySort,
            "order": "desc",
            "per_page": 100
        }, auth=requests.auth.HTTPBasicAuth(
            settings.GITHUB_USERNAME,
            settings.GITHUB_ACCESS_TOKEN)
        )

        results = queryResponse.json()

        for item in results["items"]:
            itemUpdate = dt.strptime(item['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
            itemPush = dt.strptime(item['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")

            lastUpdate = max(itemUpdate, itemPush)
            if lastUpdate >= timeNow - td(minutes=pingRange):
                updates.append(item)

        return updates

    def getUserInfo(self, url):
        """
        getUserInfo() retrieves the user data from Github users API

        :url: string, https://api.github.com/users/{user_name}
        """
        try:
            response = requests.get(url, auth=requests.auth.HTTPBasicAuth(
                settings.GITHUB_USERNAME,
                settings.GITHUB_ACCESS_TOKEN
            )).json()

            return {
                "login": response["login"],
                "id": response["id"],
                "avatar_url": response["avatar_url"],
                "html_url": response["html_url"],
                "followers": response["followers"],
                "following": response["following"],
                "bio": response["bio"],
                "public_repos": response["public_repos"],
                "created_at": dt.strptime(response["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                "updated_at": dt.strptime(response["updated_at"], "%Y-%m-%dT%H:%M:%SZ"),
            }

        except Exception as e:
            return {
                "login": "",
                "id": "",
                "avatar_url": "",
                "html_url": "",
                "followers": "",
                "following": "",
                "bio": "",
                "public_repos": "",
                "created_at": "",
                "updated_at": "",
            }

    def getlastCommit(self, url):
        """
        getUserInfo() retrieves the commit data from Github repo API

        :url: string, https://api.github.com/repos/{user_name}/{repo_nmae}/commits
        """
        try:
            response = requests.get(url, auth=requests.auth.HTTPBasicAuth(
                settings.GITHUB_USERNAME,
                settings.GITHUB_ACCESS_TOKEN)).json()

            lastCommit = response[0]

            return {
                "sha": lastCommit["sha"],
                "node_id": lastCommit["node_id"],
                "author": lastCommit["commit"]["author"]["name"],
                "message": lastCommit["commit"]["message"],
            }

        except Exception as e:
            return {
                "sha": "",
                "node_id": "",
                "author": "",
                "message": "",
            }

    def formatUpdates(self, updates):
        """
        formatUpdates() formats the filtered updates returned by Github API

        :updates: list of dictionaries, list of updates returned by Github API
        """
        formattedUpdates = []

        for item in updates:
            tmp = {}
            tmp["id"] = item["id"]
            tmp["full_name"] = item["full_name"]
            tmp["html_url"] = item["html_url"]
            tmp["description"] = item["description"]

            tmp["owner"] = self.getUserInfo(item["owner"]["url"])

            tmp["created_at"] = dt.strptime(
                item['created_at'], "%Y-%m-%dT%H:%M:%SZ")
            tmp["updated_at"] = dt.strptime(
                item['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
            tmp["pushed_at"] = dt.strptime(
                item['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")

            tmp["stargazers_count"] = item["stargazers_count"]
            tmp["watchers_count"] = item["watchers_count"]
            tmp["forks_count"] = item["forks_count"]
            tmp["open_issues_count"] = item["open_issues_count"]

            tmp["lastCommit"] = self.getlastCommit(
                item["commits_url"][:-6])

            formattedUpdates.append(tmp)

        return formattedUpdates

    def checkStringLength(self, string, maxLen):
        """
        checkStringLength() checks if a string is too long and shorten it if it excedds max length

        :string: string, target string
        :maxLen: integer, max length of the string
        """
        if (string and len(string) >= maxLen):
            return string[:maxLen] + "...(continue)"
        else:
            return string

    def formatResponseString(self, commit):
        """
        formatResponseString() formats the data retrieved by getLatestRepositories() into response string for Telegram

        :commit: dictionary, dict returned by getLatestRepositories()
        """
        resstr = ""

        lastUpdate = max(commit["updated_at"], commit["pushed_at"])
        createdAt = commit["created_at"]

        timeDelta = (dt.utcnow()-lastUpdate).seconds
        hours, remainder = divmod(timeDelta, 3600)
        minutes, seconds = divmod(remainder, 60)

        name = commit["full_name"]
        url = commit["html_url"]
        description = self.checkStringLength(commit["description"], 180)

        owner = commit["owner"]["login"]
        followers = commit["owner"]["followers"]
        bio = self.checkStringLength(commit["owner"]["bio"], 180)
        publicRepos = commit["owner"]["public_repos"]

        stargazers = commit["stargazers_count"]
        watchers = commit["watchers_count"]
        forks = commit["forks_count"]

        lastCommitAuthor = commit["lastCommit"]["author"]
        lastCommitMessage = commit["lastCommit"]["message"]

        resstr += f"Last Updated: {lastUpdate} ({hours}h {minutes}m {seconds}s ago)\n"
        resstr += f"Created At: {createdAt}\n\n"

        resstr += f"Name: {name}\n"
        resstr += f"Description: {description}\n\n"

        resstr += f"Owner: {owner} (followers: {followers})\n"
        resstr += f"Bio: {bio}\n\n"

        resstr += f"Last Commit: {lastCommitMessage}\n"
        resstr += f"Author: {lastCommitAuthor}\n\n"

        resstr += f"Stargazers: {stargazers}\n"
        resstr += f"Watchers: {watchers}\n"
        resstr += f"Forks: {forks}\n\n"

        resstr += f"URL: {url}\n"

        return resstr

    def formatTwitterString(self, commit):
        """
        formatResponseString() formats the data retrieved by getLatestRepositories() into response string for Twitter

        :commit: dictionary, dict returned by getLatestRepositories()
        """
        resstr = ""

        name = commit["full_name"]
        url = commit["html_url"]
        description = self.checkStringLength(commit["description"], 180)

        owner = commit["owner"]["login"]
        followers = commit["owner"]["followers"]
        bio = self.checkStringLength(commit["owner"]["bio"], 180)
        publicRepos = commit["owner"]["public_repos"]

        stargazers = commit["stargazers_count"]
        watchers = commit["watchers_count"]
        forks = commit["forks_count"]

        lastCommitAuthor = commit["lastCommit"]["author"]
        lastCommitMessage = commit["lastCommit"]["message"]

        resstr += f"Name: {name}\n"
        resstr += f"Description: {description}\n\n"

        resstr += f"Last Commit: {lastCommitMessage}\n"
        resstr += f"Author: {lastCommitAuthor}\n\n"

        resstr += f"Stargazers: {stargazers}\n"
        resstr += f"Watchers: {watchers}\n"
        resstr += f"Forks: {forks}\n\n"

        resstr += f"URL: {url}\n"

        return resstr

    def print(self):
        """
        print() get the latest updates from Github and print on terminal
        """
        updates = self.getLatestRepositories(
            self.language, self.searchRange, self.pingRange)
        formattedUpdates = self.formatUpdates(updates)

        for commit in formattedUpdates:
            resstr = self.formatResponseString(commit)
            print()
            print("=====================================")
            print()
            print(resstr)

    def pingTelegram(self):
        """
        pingTelegram() get the latest updates from Github and ping on Telegram
        """
        updates = self.getLatestRepositories(
            self.language, self.searchRange, self.pingRange)
        formattedUpdates = self.formatUpdates(updates)

        for commit in formattedUpdates:
            resstr = self.formatResponseString(commit)
            data = {
                "chat_id": settings.TELEGRAM_CHAT,
                "text": resstr
            }
            requests.post(settings.TELEGRAM_URL, data)

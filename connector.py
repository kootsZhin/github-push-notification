import requests
from datetime import datetime as dt, timedelta as td


class GithubConnector:
    def __init__(self):
        self.base_url = "https://api.github.com"

    def getLatestRepositories(self, language, dayBefore, timeRange):
        itemList = []

        timeNow = dt.utcnow()
        timeBefore = dt.utcnow() - td(days=dayBefore)

        isoDateNow = timeNow.strftime('%Y-%m-%d')
        isoDateBefore = timeBefore.strftime('%Y-%m-%d')

        queryString = f"pushed:{isoDateBefore}..{isoDateNow} language:{language}"
        querySort = "updated"

        queryResponse = requests.get(self.base_url + "/search/repositories", params={
            "accept": "application/vnd.github.v3+json",
            "q": queryString,
            "sort": querySort,
            "order": "desc",
            "per_page": 100
        })

        results = queryResponse.json()

        for item in results["items"]:
            itemUpdate = dt.strptime(item['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
            itemPush = dt.strptime(item['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")

            lastUpdate = min(itemUpdate, itemPush)
            if lastUpdate >= timeNow - td(hours=timeRange):
                itemList.append(item)

        return itemList

    def getFormattedUpdates(self, language, dayBefore, timeRange):
        updates = self.getLatestRepositories(language, dayBefore, timeRange)
        for item in updates:
            tmp = {}
            tmp["id"] = item["id"]
            tmp["full_name"] = item["full_name"]
            tmp["html_url"] = item["html_url"]
            tmp["description"] = item["description"]

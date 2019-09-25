# -*- coding: utf-8 -*-
""" Created by Safa Arıman on 12.12.2018 """
""" Updated by David Hollinger on 08.21.2019 """
import base64
import json
import urllib
import urllib.parse
import urllib.request
import re
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

__author__ = 'lkc0987'


class ExtensionKeywordListener(EventListener):

    def __init__(self, icon_file):
        self.icon_file = icon_file

    def on_event(self, event, extension):
        query = event.get_argument()
        regex = r".{3}-\d{1,5}"
        pattern = re.compile(regex)
        jqlQuery = ""
        if (pattern.match(query)):
            jqlQuery = "key=\"" + query + "\""
        else:
            jqlQuery = "summary~\"" + query + "\" OR text~\"" + query + "\""
        results = []

        workspace_url = extension.preferences.get('url')
        user = extension.preferences.get('username')
        password = extension.preferences.get('password')

        token = base64.b64encode(str('%s:%s' % (user, password)).encode()).decode()
        url = urllib.parse.urljoin(workspace_url, 'rest/api/latest/search')
        get_url = "%s?%s" % (url, urllib.parse.urlencode({'jql': jqlQuery}))
        req = urllib.request.Request(get_url, headers={'Authorization': 'Basic %s' % token, 'Content-Type': 'application/json'}, method="GET")

        result_types = []

        try:
            response = urllib.request.urlopen(req)
            result_types = json.loads(response.read())
        except urllib.error.HTTPError as e:
            if e.code == 401:
                results.append(
                    ExtensionResultItem(
                        name='Authentication failed.',
                        description='Please check your username/e-mail and password.',
                        icon=self.icon_file,
                        on_enter=DoNothingAction()
                    )
                )
            return RenderResultListAction(results)
        except urllib.error.URLError as e:
            results.append(
                ExtensionResultItem(
                    name='Could not connect to Jira.',
                    description='Please check your workspace url and make sure you are connected to the internet.',
                    icon=self.icon_file,
                    on_enter=DoNothingAction()
                )
            )
            return RenderResultListAction(results)
        issues = result_types.get('issues')
        for issue in issues:
            key = issue.get('key')
            title = issue.get('fields').get('summary')
            url1 = urllib.parse.urljoin(workspace_url, 'browse/%s' % key)
            results.append(
                ExtensionResultItem(
                    name=title if not key else '%s - %s' % (key, title),
                    description=key,
                    icon=self.icon_file, on_enter=OpenUrlAction(url=url1)
                )
            )

        if not results:
            results.append(
                ExtensionResultItem(
                    name="Search '%s'" % query,
                    description='No results. Try searching something else :)',
                    icon=self.icon_file,
                    on_enter=DoNothingAction()
                )
            )

        return RenderResultListAction(results)

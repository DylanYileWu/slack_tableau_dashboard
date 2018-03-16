#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 25 14:18:51 2017

@author: dylan wu

@website: yilewu.me

@linkedin:https://www.linkedin.com/in/yilewu/
"""
import requests
import xmltodict 
import os
from slackclient import SlackClient
import traceback


def main():
    ################################
    #######Parameters to change ####
    ################################
    viewToCopy= {"name_of_your_view":("name_the_pic_you_want_to_send","#slack_group")} # {key:view name in Tableau value: the file we want to name}
    tabAcct = "Tableau_Account"
    tabPwd = "Tableau_Password"
    siteDoamin = "Tableau_Domain"
    slackToken = "You_slack_token"  # found at https://api.slack.com/web#authentication
    try:
        auth = '''<tsRequest> \
          <credentials name="{0}" password="{1}" > \
            <site contentUrl="{2}" />  \
          </credentials>  \
        </tsRequest>'''.format(tabAcct,tabPwd,siteDoamin)
        
        # tableau authetication
        auth = requests.post("https://us-east-1.online.tableau.com/api/2.6/auth/signin", data = auth)
        xmlAuth = auth.text
        authDict = xmltodict.parse(xmlAuth)
        accessToken = authDict['tsResponse']['credentials']['@token']
        siteID = authDict['tsResponse']['credentials']['site']['@id']
        userID = authDict['tsResponse']['credentials']['user']['@id']
        
        # get all the dashboards with this account
        print ("gathering all the views...")
        getViews = "https://us-east-1.online.tableau.com/api/2.6/sites/{0}/views".format(siteID)
        headers = {"X-Tableau-Auth":"{0}".format(accessToken),}
        viewXML = requests.get(getViews, headers=headers).text
        views = xmltodict.parse(viewXML)
        viewList = views['tsResponse']['views']['view']
        viewIdDict = {}
        
        # loop through the dashboard list and the found the ones in the viewToCopy
        for viewItem in viewList:
                if viewItem['@name'] in viewToCopy:
                    # viewIdList = {key: view id in Tableau, value: the name we want to give}
                    viewIdDict[viewItem['@id']] = viewToCopy[viewItem['@name']]

        # query images in tableau
        params = (
            ('resolution', 'high'),
        )
        print ("saving all the images...")
        for viewID in viewIdDict:
            ######################################################################
            ### There is a chance that Tableau change their end point, be aware ##
            ######################################################################
            getImage = "https://us-east-1.online.tableau.com/api/2.6/sites/{0}/views/{1}/image".format(siteID, viewID)
            imgRequest = requests.get(getImage, headers=headers, params=params)
            fileName = '/tmp/{0}.png'.format(viewID)
            # save image on local machine
            with open(fileName, 'wb') as outFile:
                outFile.write(imgRequest.content)
        
        # connect to slack 
        print ("talking to slack...")
        sc = SlackClient(slackToken)
    
        # send images to slack 
        for imageLocation, fnameChannel in viewIdDict.iteritems():
           print sc.api_call('files.upload', channels="{0}".format(fnameChannel[1]), user = 'U552ZQ872',\
                             filename='{0}.png'.format(fnameChannel[0]), file=open("/tmp/{0}.png".format(imageLocation), 'rb'))

        # remove the images
        for viewID in viewIdDict:
            fileName = '/tmp/{0}.png'.format(viewID)
            os.remove(fileName)
    except:
        traceback.print_exc()
    finally:
        requests.post("https://us-east-1.online.tableau.com/api/2.6/auth/signout", headers = headers)
        print ("sign out")

main()

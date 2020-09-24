# coding = utf-8

import json
import os
import requests
import urllib
import urllib.request
import sys

# Shahed-DL - DrEaMTN @ Arab Extra

def dlepisode(episodeID):
    episodeBaseURL = 'https://api2.shahid.net/proxy/v2/playout/new/url/{}?download=false'.format(episodeID)

    print (episodeBaseURL)

    episodeRequest = requests.get(episodeBaseURL, allow_redirects=True)
    episodeData = json.loads(episodeRequest.content)

    if episodeData.get('faults'):
        print(episodeData['faults'][0]['userMessage'])
        return

    episodeCDN = episodeData['playout']['url']
    episodeCDNnoRestrictions = episodeCDN.split('/manifest')[0]

    episodeName = hyphen_split(hyphen_split(episodeCDN))
    episodeNameNoISM = episodeName.split('.ism')[0]

    filename = ('{}'.format(episodeNameNoISM))

    command = 'streamlink -o {0}.mp4 "{1}/manifest(format=m3u8-aapl-v3).m3u8" best'.format(
        filename, episodeCDNnoRestrictions)

    runStreamLinkCommand(command)


def dlsingleepisode():
    episodeID = input("Enter epsiode ID: ")

    dlepisode(episodeID)


def dlseries():
    seriesID = input("Enter a Shahid series ID: ")
    while not seriesID.isnumeric():
        print('Series ID must be a number')
        seriesID = input("Enter a Shahid series ID: ")

    seriesRequestBaseURL = 'https://api2.shahid.net/proxy/v2/product/id?request='
    seriesRequestParamters = {'id': seriesID,
                              'productType': 'SHOW', 'productSubType': 'SERIES'}

    seriesRequestCombined = seriesRequestBaseURL + \
                            str(json.dumps(seriesRequestParamters))

    seriesRequest = requests.get(seriesRequestCombined)
    seriesData = json.loads(seriesRequest.content)

    playlistsArray = seriesData['productModel']['season']['playlists']

    for playlist in playlistsArray:

        if 'type' in playlist:
            if playlist['type'] == 'EPISODE':
                seriesPlaylistID = playlist['id']

    seriesPlaylistRequestBaseURL = 'https://api2.shahid.net/proxy/v2/product/playlists?request='
    seriesPlaylistRequestParamters = {'playlists': [
        {'pageNumber': 0, 'pageSize': 20, 'playListId': seriesPlaylistID, 'productId': seriesID}]}

    seriesPlaylistRequestCombined = seriesPlaylistRequestBaseURL + \
                                    str(json.dumps(seriesPlaylistRequestParamters))

    playlistRequest = requests.get(seriesPlaylistRequestCombined)
    playlistData = json.loads(playlistRequest.content)

    episodesArray = playlistData
    scrapedEpisodesArray = []

    episodesCount = episodesArray['productGroups'][0]['productList']['count']
    print(f'Episodes in series: {episodesCount}\n')

    currentPageNumber = 0

    while len(scrapedEpisodesArray) < episodesCount:

        episodesArray = getEpisodesArrayData(currentPageNumber, seriesPlaylistID, seriesID)

        for episode in episodesArray:
            scrapedEpisodesArray.append(episode['id'])

        currentPageNumber += 1

    downloadEpisodesFromScrapedArray(scrapedEpisodesArray, episodesCount)

    print(f'\nScraped episodes in series: {len(scrapedEpisodesArray)}')

def downloadEpisodesFromScrapedArray(scrapedEpisodesArray, episodesCount):
    currentDownloadedEpisodesCount = 0

    for episode in scrapedEpisodesArray:
        dlepisode(episode)
        currentDownloadedEpisodesCount += 1
        print(f'Downloaded {currentDownloadedEpisodesCount} episodes out of {episodesCount}')

def getEpisodesArrayData(pageNumber, seriesPlaylistID, seriesID):
    seriesPlaylistRequestNextPageBaseURL = 'https://api2.shahid.net/proxy/v2/product/playlists?request='
    seriesPlaylistRequestNextPageParamters = {'playlists': [
        {'pageNumber': pageNumber, 'pageSize': 20, 'playListId': seriesPlaylistID, 'productId': seriesID}]}

    seriesPlaylistRequestCombined = seriesPlaylistRequestNextPageBaseURL + \
                                    str(json.dumps(seriesPlaylistRequestNextPageParamters))

    playlistRequest = requests.get(seriesPlaylistRequestCombined)
    playlistData = json.loads(playlistRequest.content)
    playlistEpisodesArray = playlistData['productGroups'][0]['productList']['products']

    return playlistEpisodesArray


def runStreamLinkCommand(command):
    print("")
    os.system(command)
    print("")


def hyphen_split(a):
    if a.count("/") == 1:
        return a.split("/")[0]
    else:
        return "/".join(a.split("/", 4)[4:])


def main():
    print("Shahed-DL - DrEaMTN @ Arab Extra")

    print("")
    print("Available options: ")
    print("1. Series")
    print("2. Episode")
    print("3. Exit")
    print("")

    chosenOption = input("Enter option: ")

    if chosenOption == '1':
        dlseries()
    elif chosenOption == '2':
        dlsingleepisode()
    elif chosenOption == '3':
        quit()


if __name__ == "__main__":
    main()

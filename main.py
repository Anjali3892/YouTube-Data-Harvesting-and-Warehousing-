from googleapiclient.discovery import build

api_key = 'AIzaSyDg3-srlMiDE9PlHIue2z6NzaNp_UpJMjE'
youtube = build('youtube', 'v3', developerKey=api_key)

def get_channel_stats(channel_id):
    
    request = youtube.channels().list(
        part="snippet, contentDetails, statistics, status, topicDetails",
        id=channel_id
    )

    response = request.execute()

    topic_categories = response['items'][0]['topicDetails']['topicCategories']

    data = {
        "Channel_Name": response['items'][0]['snippet']['title'],
        "Channel_Id": response['items'][0]['id'],
        "Subscription_Count": response['items'][0]['statistics']['subscriberCount'],
        "Channel_Views": response['items'][0]['statistics']['viewCount'],
        "Channel_Description": response['items'][0]['snippet']['description'],
        "Playlist_Id": response['items'][0]['contentDetails']['relatedPlaylists']['uploads'],
        "Channel_Status": response['items'][0]['status']['privacyStatus'],
        "Channel_Type": topic_categories[0].split('/')[-1]
    }

    return data


def get_video_ids(playlist_id):
    
    request = youtube.playlistItems().list(
        part="contentDetails",
        playlistId=playlist_id,
        maxResults=50
    )

    response = request.execute()

    video_ids = []

    for i in range(len(response['items'])):
        video_ids.append(response['items'][i]['contentDetails']['videoId'])

    next_page_token = response.get('nextPageToken')
    more_pages = True

    while more_pages:
        if next_page_token is None:
            more_pages = False
        else:
            request = youtube.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )

            response = request.execute()

            for i in range(len(response['items'])):
                video_ids.append(response['items'][i]['contentDetails']['videoId'])

            next_page_token = response.get('nextPageToken')

    return video_ids


def get_video_details(video_ids):
   
    video_stats = []

    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet, statistics, contentDetails",
            id=','.join(video_ids[i:i + 50])
        )

        response = request.execute()

        for video in response['items']:
            data = {
                "Video_Id": video['id'],
                "Video_Name": video['snippet']['title'],
                "Video_Description": video['snippet']['description'],
                "Tags": video['snippet'].get('tags'),
                "PublishedAt": video['snippet']['publishedAt'],
                "View_Count": video['statistics']['viewCount'],
                "Like_Count": video['statistics'].get('likeCount'),
                "Dislike_Count": video['statistics'].get('dislikeCount'),
                "Favorite_Count": video['statistics']['favoriteCount'],
                "Comment_Count": video['statistics'].get('commentCount'),
                "Duration": video['contentDetails']['duration'],
                "Thumbnail": video['snippet']['thumbnails']['default']['url'],
                "Caption_Status": video['contentDetails']['caption']
            }

            video_stats.append(data)

    return video_stats


def get_video_comments(video_ids):
    
    comments = []

    for video_id in video_ids:
                request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=50
            )

    while request:
                response = request.execute()

                for comment in response['items']:
                    data = {
                        'Video_Id': video_id,
                        'Comment_Id': comment['snippet']['topLevelComment']['id'],
                        'Comment_Text': comment['snippet']['topLevelComment']['snippet']['textOriginal'],
                        'Comment_Author': comment['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                        'Comment_PublishedAt': comment['snippet']['topLevelComment']['snippet']['publishedAt']
                    }
                    comments.append(data)

                if 'nextPageToken' in response:
                    request = youtube.commentThreads().list(
                        part="snippet",
                        textFormat="plainText",
                        videoId=video_id,
                        maxResults=50,
                        pageToken=response.get('nextPageToken')
                    )
                else:
                    break


    return comments


def bind_data(channel_id):
    channel_stats = get_channel_stats(channel_id)
    playlist_id = channel_stats['Playlist_Id']
    video_ids = get_video_ids(playlist_id)
    video_details = get_video_details(video_ids)
    video_comments = get_video_comments(video_ids)

    data = {
        "Channel_Name": channel_stats
    }

    for i, video in enumerate(video_details, 1):
        video_id = f"Video_Id_{i}"
        comments = {}

        for comment in video_comments:
            if comment == "Comments disabled" or comment["Video_Id"] == video["Video_Id"]:
                comment_id = f"Comment_Id_{len(comments) + 1}"
                comments[comment_id] = {
                    "Comment_Id": comment.get("Comment_Id", "Comments disabled"),
                    "Comment_Text": comment.get("Comment_Text", "Comments disabled"),
                    "Comment_Author": comment.get("Comment_Author", "Comments disabled"),
                    "Comment_PublishedAt": comment.get("Comment_PublishedAt", "Comments disabled")
                }

        video["Comments"] = comments
        data[video_id] = video

    return data

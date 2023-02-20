import discord
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio

client = discord.Client(intents=discord.Intents.all())

TOKEN = "Discord_Token"
client_id = "Spotify_client_id"
client_secret = "Spotify_client_secret"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='!info in BLM'))

@client.event
async def on_message(message):
    if message.content.startswith('!similar'):
        query = message.content[9:]
        response = get_similar_tracks(query)
        embed = discord.Embed(title="Spotify Recommendations", description=response, color=0x1DB954)
        await message.channel.send(embed=embed)
    elif message.content.startswith('!go'):
        activity = message.author.activity
        if activity and activity.type == discord.ActivityType.listening and activity.title:
            query = activity.title
            response = get_similar_tracks(query)
            embed = discord.Embed(title="Spotify Recommendations", description=response, color=0x1DB954)
            await message.channel.send(embed=embed)
        else:
            # keine passende Aktivität gefunden
            response = "You are not currently listening to Spotify!"
            await message.channel.send(response)
    elif message.content.startswith('!scan') and any(role.name == 'Business-member' for role in message.author.roles):
        activity_saver(message)
    elif message.content.startswith('!bpm'):
            activity = message.author.activity
            if activity and activity.type == discord.ActivityType.listening and activity.title:
                track = activity.title
                artist = activity.artist
                query = f'{track} - {artist}'
                response = get_bpm(query)
                formated = f'Song: {track} \r Artist(s): {artist} \r BPM: {response}'
                embed = discord.Embed(title=query, description=formated, color=0x1DB954)
                await message.channel.send(embed=embed)
            else:
                # keine passende Aktivität gefunden
                response = "You are not currently listening to Spotify!"
                await message.channel.send(response)
    elif message.content.startswith('!info'):
        help_embed = discord.Embed(title="Help", description="Here are the available commands:", color=0x1DB954)
        help_embed.add_field(name="!similar <song_title> <song_artist>", value="Get similar tracks based on a given song.", inline=False)
        help_embed.add_field(name="!go", value="Get similar tracks based on your current Spotify activity.", inline=False)
        help_embed.add_field(name="!bpm", value="Get current Spotify Song BPM", inline=False)
        help_embed.add_field(name="!scan/!stop", value="Start/Stop scanning Spotify Activities.", inline=False)
        help_embed.add_field(name="!info", value="Get a list of available commands.", inline=False)
        await message.channel.send(embed=help_embed)
        

def get_similar_tracks(query):
    result = sp.search(q=query, type='track')
    if result['tracks']['total'] > 0:
        track_id = result['tracks']['items'][0]['id']
        similar_tracks = sp.recommendations(seed_tracks=[track_id], limit=7)
        return format_similar_tracks_response(query, similar_tracks)
    else:
        return "No tracks found matching your query."

def format_similar_tracks_response(query, similar_tracks):
    response = "Similar tracks to " + query + ":\n"
    for i, track in enumerate(similar_tracks['tracks']):
        track_name = track['name']
        track_artist = track['artists'][0]['name']
        track_url = track['external_urls']['spotify']
        track_bpm = get_bpm(track_name, track_artist)
        response += str(i+1) + ". " + "[" + track_name + " by " + track_artist +"](" + track_url + ")" + " - BPM: " + str(track_bpm) + "\n"
    return response

async def activity_saver(message):
    # continuously update list of user's Spotify activities
    spotify_activity_list = []
    while True:
        # check for stop command
        if message.content.startswith('!stop'):
            await message.channel.send('Scannen beendet.')
            print(spotify_activity_list)
            break
        # update activity list for each user on the server
        for member in message.guild.members:
            if member.activity and member.activity.type == discord.ActivityType.listening:
                track = member.activity.title
                artist = member.activity.artist
                query = f'{track} {artist}'
                bpm = get_bpm(query)
                activity_info = {"user_id": member.id, "user_name": member.name, "song_title": track, "song_artist": artist, "bpm": bpm}
                spotify_activity_list.append(activity_info)
                # wait for a short time before checking the next user
                await asyncio.sleep(2)
                if message.content.startswith('!stop'):
                    await message.channel.send('Scannen beendet.')
                    print(spotify_activity_list)
                    break
    # do something with the final spotify_activity_list

def get_bpm(query):
    #query = f"track:{title} artist:{artist}"
    results = sp.search(q=query, type="track", limit=1)

    if results["tracks"]["items"]:
        track_id = results["tracks"]["items"][0]["id"]
        track_features = sp.audio_features([track_id])[0]

        if track_features["tempo"]:
            bpm = round(track_features["tempo"])
            return bpm
        
def get_bpm(track_name, artist_name):
    query = f"{track_name} {artist_name}"
    result = sp.search(q=query, type='track')
    if result['tracks']['total'] > 0:
        track_id = result['tracks']['items'][0]['id']
        track_features = sp.audio_features([track_id])[0]
        if track_features and 'tempo' in track_features:
            return round(track_features['tempo'])
    return "N/A"

client.run(TOKEN)

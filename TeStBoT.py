import discord
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
import threading
import tracemalloc

client = discord.Client(intents=discord.Intents.all())

TOKEN = "MTA3NTQ0MTMyMzQ0NTg2NjU4OA.G265SF.CkPz6HpEKtzBMCEFlEFen8gHPIE_8VnBmr59dM"
client_id = "40a977e419844aadab020e6fd49da439"
client_secret = "4249888ce8f94872a9c5b9b4991bc3f1"
is_thread_running = False
task = None

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
            track = activity.title
            artist = activity.artist
            query = f'{track} - {artist}'
            response = get_similar_tracks(query)
            embed = discord.Embed(title="Spotify Recommendations", description=response, color=0x1DB954)
            await message.channel.send(embed=embed)
        else:
            # keine passende Aktivität gefunden
            response = "You are not currently listening to Spotify!"
            await message.channel.send(response)

    elif message.content.startswith('!scan') and any(role.name == 'Business-member' for role in message.author.roles):

        await start_activity(message,1)   #(message, Start[1] / Stop[2])

    elif message.content.startswith('!stopp') and any(role.name == 'Business-member' for role in message.author.roles):

        await start_activity(message,2)   #(message, Start[1] / Stop[2])

    elif message.content.startswith('!bpm'):
            activity = message.author.activity
            if activity and activity.type == discord.ActivityType.listening and activity.title:
                track = activity.title
                artist = activity.artist
                query = f'{track} - {artist}'
                response = get_bpm2(query)
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
        
def start_activity_saver(message):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(activity_saver(message))

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
    while True:  
        current, peak = tracemalloc.get_traced_memory()
        print(f"Speichernutzung: {current / 10**6}MB; Spitzenwert: {peak / 10**6}MB.")
        print(f"Momentan: {current}  Höchstwert: {peak}")
        await asyncio.sleep(2)  # continuously update list of user's Spotify activities
        spotify_activity_list = []
        for member in message.guild.members:
            if member.activity and member.activity.type == discord.ActivityType.listening and member.activity.name == 'Spotify':

                if member.activity.type == discord.ActivityType.listening:
                    track = member.activity.title
                    artist = member.activity.artist
                    query = f'{track} {artist}'
                    bpm = get_bpm2(query)
                    activity_info = {"user_id": member.id, "user_name": member.name, "song_title": track, "song_artist": artist, "bpm": bpm}
                    spotify_activity_list.append(activity_info)
                # wait for a short time before checking the next user
                    await asyncio.sleep(1)
                print (spotify_activity_list)
                
# do something with the final spotify_activity_list

def get_bpm2(query):
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

async def start_activity(message, state):
    global is_thread_running
    global task

    if state == 1:
        if is_thread_running == False:
            task = asyncio.create_task(activity_saver(message))
            await asyncio.sleep(3)
            await message.channel.send('Scann gestartet.')
            is_thread_running = True
        else:
            await message.channel.send('Scann läuft...')

    elif state == 2:
        if is_thread_running == True:
            task.cancel()  # Abbrechen der Task
            await message.channel.send('Scann gestoppt')
            is_thread_running = False
        else:
            await message.channel.send('Scann läuft nicht!')

    return is_thread_running


client.run(TOKEN)

import discord
from discord.ext import commands
#from discord_components import DiscordComponents, Button, ButtonStyle
from discord.ui import Select, View
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
import threading
import tracemalloc
import openai

client = discord.Client(intents=discord.Intents.all())

TOKEN = "DiscordToken"
client_id = "ClientIDSpotify"
client_secret = "ClientSECRETSpotify"
OpenAI_api_key = "OpenAiToken"

is_thread_running = False
task = None

preprompt = {'Title1': 'Beschreibung1',
             'Title2': 'Beschreibung2',
             'Title3': 'Beschreibung3',
             'Title4': 'Beschreibung4',
             'Title5': 'Beschreibung5',
             'Title6': 'Beschreibung6'}

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
    elif message.content.startswith('!gpt'):
        #selected_prompt = await change_persona(message)
        await change_persona2(message)
        #await message.channel.send('Schreibe mir deinen prompt :D')
        #query = await message.content
       # query = message.content[5:]
        #get_openai_response(pre_prompt, query)
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
    """
    This function starts an asyncio event loop that continuously retrieves and saves the Spotify listening activities of all members in a Discord server.

    Args:
        message (discord.Message): The message object that triggered the function.

    Returns:
        None.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(activity_saver(message))

def get_similar_tracks(query):
    """
    Retrieves a list of similar tracks to the queried track and formats the response.

    Args:
        query (str): A string representing the track name and/or artist name to search for.

    Returns:
        str: A formatted string containing similar tracks to the queried track.
    """
    result = sp.search(q=query, type='track')
    if result['tracks']['total'] > 0:
        track_id = result['tracks']['items'][0]['id']
        similar_tracks = sp.recommendations(seed_tracks=[track_id], limit=7)
        return format_similar_tracks_response(query, similar_tracks)
    else:
        return "No tracks found matching your query."


async def change_persona2(message):
    options = [
        discord.SelectOption(label='Beschreibung', value='Titel'),
        discord.SelectOption(label='Option 2', value='option2'),
        discord.SelectOption(label='Option 3', value='option3'),
    ]

    select = discord.ui.Select(
        placeholder='Wähle eine Option aus', 
        options=options
    )

    async def on_select(interaction):
        #get_openai_response(select.values[0])
        #Start loop for conversation
        await interaction.response.send_message(f'Du hast {select.values[0]} ausgewählt.')

    select.callback = on_select

    view = discord.ui.View()
    view.add_item(select)

    await message.channel.send('Wähle eine Option:', view=view)


async def change_persona(message):
    '''
    Diese Funktion soll einen Embeded Dropdown in einem Text channel erstellen.
    Die Auswahl hat verschiedene "Persönlickeiten" die im Backend bestimmte Persönlichkeits Prompts ausführt.
    
    '''
    options = [discord.SelectOption(label=k, value=k) for k in preprompt.keys()]
    select = discord.ui.Select(options=options, placeholder='Wähle ein Prompt aus', min_values=1, max_values=1)

    view = discord.ui.View()
    view.add_item(select)

    embed = discord.Embed(title='Wähle ein Prompt aus', description='Bitte wähle ein Prompt aus der Liste aus:')

    msg = await message.channel.send(embed=embed, view=view)
    try:
        interaction = await client.wait_for('select_option', timeout=30.0, check=lambda i: i.message.id == msg.id)
        selected_prompt = preprompt[interaction.values[0]]
        await message.channel.send(selected_prompt)
    except asyncio.TimeoutError:
        await message.channel.send('Timeout')


def get_token_length(prompt):
    """
    Diese Funktion berechnet die Tokenlänge der Eingabe.

    Args:
        prompt (str): Die Eingabe, deren Tokenlänge berechnet werden soll.

    Returns:
        int: Die Tokenlänge der Eingabe.
    """
    openai.api_key = OpenAI_api_key # Fügen Sie hier Ihren OpenAI-API-Schlüssel ein.
    token_count = openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        max_tokens=0,
        n=1,
        stop=None,
        temperature=0
    ).choices[0].text.count('\n') + 1
    return token_count

def insert_value_at_token_length(prompt, token_length, value, lst):
    """
    Diese Funktion fügt einen Wert in eine Liste ein, wenn eine bestimmte Tokenlänge erreicht wird.

    Args:
        prompt (str): Die Eingabe, deren Tokenlänge überwacht werden soll.
        token_length (int): Die Tokenlänge, bei der der Wert in die Liste eingefügt werden soll.
        value (any): Der Wert, der in die Liste eingefügt werden soll.
        lst (list): Die Liste, in die der Wert eingefügt werden soll.

    Returns:
        list: Die aktualisierte Liste.
    """
    length = get_token_length(prompt)
    if length == token_length:
        lst.append(value)
    return lst

def get_prompt_length(prompt):
    """
    Diese Funktion berechnet die Länge der Eingabe in Token.

    Args:
        prompt (str): Die Eingabe, deren Tokenlänge berechnet werden soll.

    Returns:
        int: Die Tokenlänge der Eingabe.
    """
    openai.api_key = OpenAI_api_key # Fügen Sie hier Ihren OpenAI-API-Schlüssel ein.
    token_count = openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        max_tokens=0,
        n=1,
        stop=None,
        temperature=0
    ).choices[0].text.count('\n') + 1
    return token_count

def split_prompt_by_length(prompt, max_length):
    """
    Diese Funktion teilt eine Eingabe in mehrere Teile auf, falls sie eine bestimmte Tokenlänge überschreitet.

    Args:
        prompt (str): Die Eingabe, die aufgeteilt werden soll.
        max_length (int): Die maximale Tokenlänge pro Teil.

    Returns:
        list: Eine Liste der aufgeteilten Eingabe.
    """
    token_count = get_prompt_length(prompt)
    if token_count <= max_length:
        return [prompt]
    else:
        split_prompts = []
        prompt_parts = prompt.split()
        while len(prompt_parts) > 0:
            split_prompt = ' '.join(prompt_parts[:max_length])
            split_prompts.append(split_prompt)
            prompt_parts = prompt_parts[max_length:]
        return split_prompts

def get_openai_response(querytype, query):
    """
    Diese Funktion gibt die OpenAI-Antwort basierend auf einer Eingabe zurück.

    Args:
        querytype (str): Der Typ der Anfrage.
        query (str): Die Eingabe für die Anfrage.

    Returns:
        str: Die OpenAI-Antwort.
    """
    openai.api_key = OpenAI_api_key
    max_tokens = 1024
    prompt_parts = split_prompt_by_length(f"{querytype} {query}", max_tokens)
    completions = []
    for part in prompt_parts:
        completion = openai.Completion.create(
            engine="davinci",
            prompt=part,
            max_tokens=max_tokens,
            n=1,
            stop=None,
            temperature=0.5
        ).choices[0].text.strip()
        completions.append(completion)
    response = ' '.join(completions)
    return response

def format_similar_tracks_response(query, similar_tracks):
    """
    Diese Funktion gibt eine formatierte Antwort auf eine Anfrage ähnlicher Songs zurück.

    Args:
        query (str): Die Suchanfrage, die die ähnlichen Songs ausgelöst hat.
        similar_tracks (dict): Eine Spotify-API-Antwort, die eine Liste von ähnlichen Tracks enthält.

    Returns:
        str: Eine formatierte Antwort, die die ähnlichen Songs auflistet.
    """
    response = "Similar tracks to " + query + ":\n"
    for i, track in enumerate(similar_tracks['tracks']):
        track_name = track['name']
        track_artist = track['artists'][0]['name']
        track_url = track['external_urls']['spotify']
        track_bpm = get_bpm(track_name, track_artist)
        response += str(i+1) + ". " + "[" + track_name + " by " + track_artist +"](" + track_url + ")" + " - BPM: " + str(track_bpm) + "\n"
    return response

async def activity_saver(message):
    """
    Diese asynchrone Funktion verfolgt die Spotify-Aktivitäten von Benutzern in einer Discord-Gilde und speichert sie in einer Liste.

    Args:
        message (discord.Message): Die Nachricht, die den Befehl zum Starten der Überwachung enthält.

    Returns:
        None: Diese Funktion gibt nichts zurück.
    """
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
    """
    Diese Funktion ruft die Beats pro Minute (BPM) für einen gegebenen Song-Titel und Künstler mithilfe der Spotify API ab.

    Args:
        query (str): Die Suchanfrage, die den Titel und Künstler des Songs enthält.

    Returns:
        Union[int, None]: Wenn die BPM abgerufen werden konnten, gibt die Funktion die BPM als Integer zurück. Andernfalls gibt die Funktion None zurück.
    """
    #query = f"track:{title} artist:{artist}"
    results = sp.search(q=query, type="track", limit=1)

    if results["tracks"]["items"]:
        track_id = results["tracks"]["items"][0]["id"]
        track_features = sp.audio_features([track_id])[0]

        if track_features["tempo"]:
            bpm = round(track_features["tempo"])
            return bpm
        
def get_bpm(track_name, artist_name):
    """
    Diese Funktion ruft die Beats pro Minute (BPM) für einen gegebenen Song-Titel und Künstler mithilfe der Spotify API ab.

    Args:
        track_name (str): Der Titel des Songs.
        artist_name (str): Der Name des Künstlers.

    Returns:
        Union[int, str]: Wenn die BPM abgerufen werden konnten, gibt die Funktion die BPM als Integer zurück. Andernfalls gibt die Funktion "N/A" zurück.
    """
    query = f"{track_name} {artist_name}"
    result = sp.search(q=query, type='track')
    if result['tracks']['total'] > 0:
        track_id = result['tracks']['items'][0]['id']
        track_features = sp.audio_features([track_id])[0]
        if track_features and 'tempo' in track_features:
            return round(track_features['tempo'])
    return "N/A"

async def start_activity(message, state):
    """
    This function is used to start or stop the activity_saver task that constantly checks and logs user's Spotify activities in a Discord server.

    Parameters:
    - message: A Discord message object that triggers the function.
    - state: An integer representing the state of the activity_saver task. 1 for starting the task, 2 for stopping it.

    Returns:
    - A boolean value indicating whether the activity_saver task is running or not.
    """
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

#Analyzer Discord Bot
====================

Analyzer is a Discord bot designed to enhance the music experience of users on Discord servers. This bot provides features such as recommending similar tracks to a given song, detecting the beats per minute of a current song, and continuously scanning users' Spotify activities.

Features
--------

*   Recommend similar tracks to a given song
*   Detect the beats per minute (BPM) of a current song
*   Continuously scan users' Spotify activities

Usage
-----

To use the bot, enter any of the following commands in a text channel:

*   `!similar <song_title> <song_artist>` - Get similar tracks based on a given song.
*   `!go` - Get similar tracks based on your current Spotify activity.
*   `!bpm` - Get the BPM of the song you're currently listening to.
*   `!scan` - Start scanning users' Spotify activities.
*   `!stop` - Stop scanning users' Spotify activities.
*   `!info` - Get a list of available commands.

**Note:** The `!scan` command can only be used by users with the `Business-member` role.

How to Run
----------

To run the Analyzer Discord bot, you'll need to follow these steps:

1.  Clone this repository to your local machine.
2.  Install the required dependencies using `pip install -r requirements.txt`.
3.  Add your bot token and Spotify credentials to the `config.py` file.
4.  Run `python bot.py` to start the bot.

Examples
--------

Here are some examples of how the bot works:

#### `!similar`

![Similar Tracks](images/similar.png)

#### `!go`

![Current Activity](images/current.png)

#### `!bpm`

![Current BPM](images/bpm.png)

#### `!info`

![Command List](images/info.png)

Contributing
------------

If you'd like to contribute to the Analyzer Discord bot, please follow these steps:

1.  Fork this repository.
2.  Create a new branch.
3.  Make your changes and commit them.
4.  Push your changes to your fork.
5.  Create a pull request.

Credits
-------

*   [Discord.py](https://discordpy.readthedocs.io/en/stable/)
*   [Spotipy](https://spotipy.readthedocs.io/en/2.18.0/)

![Kamyroll_Python](/Presentation/img_title.png)

## Description
Kamyroll-python is the python version of the program used in the application [Kamyroll](https://github.com/hyugogirubato/Kamyroll). This will allow you to download the videos and subtitles proposed by the Crunchyroll catalog or MP4 and ASS format to allow you to view the videos on all your devices without connection.
 
## Features
- Download videos in all resolutions
- Download subtitles in all languages
- Search for videos
- Compatible with or free or premium account
- Use a proxy to unblock the entire catalog
- Available for all platforms (macOS, Windows, Linux, etc.)
- Download all available episodes and movies
- Videos in mp4, mkv with or without Hardsub
- Premium bypass (windows version only)

## Requirements
- [ffmpeg](https://www.ffmpeg.org)
- [Python](https://www.python.org/downloads) 3+

### Installation
```bash
pip install kamyroll_python
```

## Information
 - To use the script log in with your email or username and your Crunchyroll password.
 - Configure your configuration file according to your preferences.
 - If you don't have Python, you can use the compiler version for Windows.
 - Use the premium bypass to download the premium videos.
 - The premium bypass uses a premium pay account dedicated to this use. It is in no way a crack of the site or the API.

## Preferences

#### Video resolution

Resolution | Quality
------------ | -------------
"1080" | FHD
"720" | HD
"480" | SD
"360" | SD
"240" | SD

#### Subtitle language 

Language | Title
------------ | -------------
"" | Without subtitles
"en-US" | English (US)
"en-GB" | English (UK)
"es-419" | Español
"es-ES" | Español (España)
"pt-BR" |Português (Brasil)
"pt-PT" | Português (Portugal)
"fr-FR" | Français (France)
"de-DE" | Deutsch
"ar-SA" | العربية
"it-IT" | Italiano
"ru-RU" | Русский

## Proxy configuration
Secure proxy compatible with Crunchyroll: https://github.com/Snawoot/hola-proxy
![proxy_example](/Presentation/img_proxy.png)

#### Command
- RED: Selected region
  
#### Proxy in $HOME/.config/kamyroll.json
- GREEN: uuid
- BLUE: agent\_key
- PURPLE: host
- YELLOW: port

## Examples

### Login with ID
```
kamyroll --login "MAIL:PASSWORD"
```
or
```
kamyroll -l "MAIL:PASSWORD"
```

### Login with configured ID
```
kamyroll --connect
```
or
```
kamyroll -c
```

### Premium bypass (Windows version only)
```
kamyroll --bypass
```
or
```
kamyroll -b
```

### Search a series, films, episode
```
kamyroll --search "QUERY"
```

### Show seasons of a series
```
kamyroll --season "SERIES_ID"
```
or
```
kamyroll -s "SERIES_ID"
```

### Show episodes of a season
```
kamyroll --episode "SEASON_ID"
```
or
```
kamyroll -e "SEASON_ID"
```

### Show movies from a movie list
```
kamyroll --movie "MOVIE_ID"
```
or
```
kamyroll -m "MOVIE_ID"
```

### Download an episode or movie
```
kamyroll --download "EPISODE_ID or MOVIE_ID"
```
or
```
kamyroll -d "EPISODE_ID or MOVIE_ID"
```

---
*This script was created by the [__Nashi Team__](https://sites.google.com/view/kamyroll/home).  
Find us on [discord](https://discord.com/invite/g6JzYbh) for more information on projects in development.*

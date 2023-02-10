<a name="readme-top"></a>
# Discord Resy Reservation Monitor

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#introduction">Introduction</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li><a href="#getting-started">Getting Started</a></li>
    <li><a href="#usage">Usage</a></li>
  </ol>
</details>

## Introduction
This is a Discord bot designed to alert and open reservation link directly from [Resy](https://resy.com/) using the [Resy API](http://subzerocbd.info/). New reservations usually become available on a daily basis. Some restaurants may vary on what time and how many days out reservations are made available. When running the bot, prompts will appear to confirm the location and restaurant before monitoring. This can be left to run in the backgroud and search for available reservation, it will automatically ping via Discord and open the available reservation link.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

* [Python][Python-url]
* [Discord.py][Discord.py-url]
* [Google Maps Platform][GoogleMaps-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started
You need to provide a few values before running the bot. The required properties that need to be provided can be found at the top of the `main.py` file before it can be used. For clarity, I will go in depth on how to get these parameters.
* **DISCORD_WEBHOOK_URL** - You will need to create a webhook in your Discord server. Proceed to hover over the channel and select on the settings. Navigate to Integrations and select `Create Webhook`. After creating, select it and name the webhook `Resy Webhook`. Then copy webhook url and paste it in the file.
* **TOKEN** - For this step, you will need to watch the following Youtube video on how to create a Discord bot to add to your server with the correct authorizations. Please make sure follow only these parts of the Youtube video: `Geting started` and `Inviting the bot to our server`. Due to copyrights, please search `Create Your Own Discord Bot in Python  Tutorial` on YouTube and follow the instructions. The token here will be the Discord bot token.
* **CHANNEL** - Right click the channel you invited the bot and copy the channel ID.
* **RESY_API** - Your user profile API key. Can be found once you're logged into Resy in most `api.resy.com` network 
calls (i.e. Try they `/find` API call when visiting a restaurant). Open your web console and look for a request header 
called `authorization`.
* **GOOGLE_MAPS_API** - Follow the instruction from Google Maps Platform on creating an API key and paste it in the file after. [Google Maps](https://developers.google.com/maps/documentation/embed/get-api-key#:~:text=Go%20to%20the%20Google%20Maps%20Platform%20%3E%20Credentials%20page.&text=On%20the%20Credentials%20page%2C%20click,Click%20Close.)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage
Please open the `main.py` file in an environment capable running python3 code. After setting up the parameters and adding the bot to your Discord serer and channel, run it! Follow the prompts asked in the channel and hopefully you are able to land a reseration.
Best of luck to you!

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS -->
[Discord.py.com]: https://discordpy.readthedocs.io/en/stable/_images/snake_dark.svg](https://wasimaster.gallerycdn.vsassets.io/extensions/wasimaster/discord-py-snippets/1.7.0/1668862916012/Microsoft.VisualStudio.Services.Icons.Default)
[Discord.py-url]: https://discordpy.readthedocs.io/en/stable/
[GoogleMaps-url]:https://developers.google.com/maps
[Python-url]:https://www.python.org/

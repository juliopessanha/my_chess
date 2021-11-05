# my_chess
Daily downloads all my chess.com games, organize the information and loads them in a database where I can access using Power BI. That's my nerdy way to understand my chess errors and improve my gameplay

## Chess and Data

Chess is a game based on pattern recognition. A huge part of a player's improvement comes from revisiting your own games and understanding what you did wrong and what could be done differently.

Chess.com, the site where I play, is the most famous chess platform in the planet. The site itself provides game statistics so you can use it to play better. The site also provides an API with which you can access and download data from any game in their database. As a nerd who's willing to work with data, I'm joining both topics I love: chess and study. I made this code so I could dig even deeper into my own games.

## Code Concept

This code will download and save every daily and live game from a given player. Then, it will read every file, transform the plain text data into a tabular and more organized data and upload it into my Data Warehouse where I access using Power BI. It's currently made to fit my own necessities, but I plan to make a version to fit everyone's needs.

### Chess.com API:

https://www.chess.com/news/view/published-data-api

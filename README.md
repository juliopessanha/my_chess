# my_chess
That downloads all my chess.com games daily, organize the information and loads them in a database where I can access using Power BI. That's my nerdy way to understand my chess errors and improve my gameplay

## Chess and Data

Chess is a game based on pattern recognition. A huge part of a player's improvement comes from revisiting your own games and understanding what you did wrong and what could be done differently.

Chess.com, the site where I play, is the most famous chess platform in the planet. The site itself provides game statistics so you can use it to play better. The site also provides an API with which you can access and download data from any game in their database. As a nerd who's willing to work with data, I'm joining both topics I love: chess and study. I made this code so I could dig even deeper into my own games.

## Code Concept

This code will download and save every daily and live game from a given player. Then, it will read every file, transform the plain text data into a tabular and more organized data and upload it into my Data Warehouse where I access using Power BI. It's currently made to fit my own necessities, but I plan to make a version to fit everyone's needs.

### Explaining the Code

1. The code accesses the https://api.chess.com/pub/player/hallsand/games/archives (using mine as a reference).
    - That page shows all subsequent links. Chess.com devides them by month in a json format;
    - Eg: https://api.chess.com/pub/player/hallsand/games/2021/09 are the games I played in September of 2021.
  
2. It checks if the player folder and month files exist.
    - If the player folder doesn't exist, the code creates it;
    - If there's a new month file, it saves;
    - If there's no new month file, it will delete the last one and save it again;
       - If we're in September, the code will delete the September file and save a new one to get newer games.

It's important to understand that the code downloaded the games as a plain text file with all the games you played in every single month. Those files must be transformed from plain text to tabular data.
      
3. Transforming plain text into tabular data using the transform_data() function.
    - The code reads all the month files, one by one, extract the usefull data and turn every single game into a list;
       - The list has the following order: [player, playerColor, oponent, result, winningReason, playerElo, oponentElo, timeControl, date, time, opening, pgn, id]
           - Player - Player's nickname;
           - playerColor - Player's color (either white or black);
           - oponent - Opponent's nickname (I know I misspelled it)
           - result - If the player won, lose or drew;
           - winningReason - If the result was by resignation, timeout or checkmate;
           - playerElo - The player's ELO at the beggining of the game;
           - oponentElo - The opponent's ELO;
           - timeControl - Game's time control (300, 600+5, and so on);
           - date - The date the game was played;
           - time - the UTC-3 time the game was played;
           - opening - Which opening the players played;
           - PGN - The game PGN (it's a chess' specific format to catalog games);
           - id - The game ID (the end of the game URL)
                   
    - Those game lists are appended together into a Pandas dataframe;

4. Counting how many times I moved each piece using the pieceMoveCounter() function.
    - That function receives a PGN formated game and counts how many times each piece was moved;
    - It appends each individual game into a python dictionary; 
       - The dictionary names uses the chess notation. Q stands for Queen, N for Knight and so on.
    - That function is called at the end of each transform_data() call;
    
5. Database load.
    - After all the extraction and transformation, the code will load the data into a MariaDB database hosted in a AWS RDS server.
       - if the game already exists in the server, it will not be uploaded;
       - I use the number provided by the end of a chess.com game URL (https://www.chess.com/game/live/27993594069) as a Primary Key ID.
    - Then the piece movement count is uploaded to another table in the same database.

### Chess.com API:

https://www.chess.com/news/view/published-data-api

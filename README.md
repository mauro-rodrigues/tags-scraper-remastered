# tags-scraper-remastered
Tags Scraper Remastered allows its users to fetch a given song's tags (Artist, Title, Album, Year, Track, Album Artist, Genre, Cover Art) automatically, requiring just the artist's name and the song's name: 
> Eminem - Beautiful

It utilizes Deezer's API to retrieve the data and is able to distinguish if a song has more than one genre, if a song or album have multiple artists and, if the song is a single, it will fetch the corresponding Cover Art and state it's a single in the Album tag. It takes as reference the folder where the script is placed and, using the syntax (Artist - Song) with .mp3 files, fetches every song's tags and edits the files automatically, organising the songs by artist and album folders.

Simply copy the example songs from testing folder into the root folder and run the script.

# WTA Scrapper

A scrapper that retrieves matches from the a player's WTA page


## Getting started

Using the following will scrap the HTML page and build the matches.

```
wta = MatchScrapper(filename='file_to_scrap.html')
wta.build('player-matches__tournament', player_name='Eugenie Bouchard', date_of_birth='1994-02-25')
```

### Writing to a JSON file

```
wta.write_values_to_file()
```


<p align="left">
<img src="https://github.com/ConnorSMaynes/allacronyms/blob/master/allacronyms/static/logo.jpeg" alt="AllAcronyms Unofficial API" >
</p>

An unofficial api to allacronyms.com. Lookup / expand abbreviations. Lookup definitions of abbreviations.

## Attributes / Methods

- `categories` : Get a list of categories abbreviations can fall under / be searched under.
- `getTopics` : Search for topics an abbreviation / definition falls under.
  - Keywords : string of keywords for either an abbreviation / definition you want to search for
  - Category : The category to search for the topics under
- `search` : Search for an abbreviation / definition ( automatically detected which one you enter )
  - Keywords : The abbreviation / definition to search for.
  - Category : The category to search under.
  - Topic : The topic to filter the results by.
  - Quantity : the number of abbreviations to return. Defaults to 1.  
- `getRandom` : get random abbreviations list

### Classes / Objects
- `AllAcronyms` : the main class for querying the site.
- `Abbreviation` : named tuple that stores info related to each abbreviation.
  - rating : the rating given to an abbreviation by the users of AllAcronyms.com.
  - confidence : the confidence ( ratio of this abbreviation's rating to sum of ratings returned in search results )
  - definition : the definition of the abbreviation
  - abb : the abbreviation

## Installation

```bash
pip install git+git://github.com/ConnorSMaynes/allacronyms
```

## Usage

```python
from allacronyms import AllAcronyms

from tabulate import tabulate
acron = AllAcronyms()

# GET RANDOM ABBREVIATION
Abbs = acron.getRandom()
print( tabulate( Abbs, headers=Abbs[0]._fields ) )

# GET LIST OF AVAILABLE CATEGORIES
Categories = acron.categories
print( tabulate( [ [ x ] for x in Categories ], headers=['Categories'] ) )

# SEARCH FOR DEFINITION
Abb = acron.search( Keywords='FOR'
                  ,Category='Organizations'
                  ,Topic='Friendship' )
if Abb != None:
    print( Abb.definition )

# SEARCH FOR ABBREVIATION
Abb = acron.search( Keywords='Application Programming Interface' )
if Abb != None:
    print( Abb.abb )
    print( Abb.definition )

# SEARCH FOR TOPICS ABBREVIATION / DEFINITION FALLS UNDER
Topics = acron.getTopics( Keywords='Peanut Butter and Jelly' )
print( tabulate( [ [ x ] for x in Topics ], headers=['Topics'] ) )

# SEARCH FOR TOP ABBREVIATIONS / DEFINITIONS
Abbs = acron.search( Keywords='YOLO', Quantity=10 )
if len( Abbs ) > 0:
    print( tabulate( Abbs, headers=Abbs[0]._fields ) )
```

## Similar Projects

This project was inspired by others:
- [xpansion](https://github.com/mscienski/xpansion)

## License

Copyright © 2018, [ConnorSMaynes](https://github.com/ConnorSMaynes). Released under the [MIT](https://github.com/ConnorSMaynes/allacronyms/blob/master/LICENSE).


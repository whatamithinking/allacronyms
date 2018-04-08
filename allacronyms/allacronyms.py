
import requests, re
from lxml.etree import HTML as get_xml
from collections import OrderedDict, namedtuple

SITE = {
    'root'          :   'https://www.allacronyms.com'
    ,'search'       :   '/aa-searchme?f=h&q={keywords}&cat={icategory}'
    ,'top_topics'   :   '/aa-topics'
    ,'random'       :   '/aa-random-term?nocache=1'
}

Abbreviation = namedtuple( 'Abbreviation', 'rating confidence definition abb' )

class AllAcronyms():
    '''
    Purpose:    The purpose of this class is to function as an unofficial API
                to the website allacronyms.com. It can get categories, topics,
                and generally search the site for abbreviations / definitions.
                The site automatically determines if a definition or abbreviation
                has been searched for.
    '''

    def __init__(self):
        self._categories = None

    def _getCategories( self ):
        '''
        Purpose:    Get all available categories, in the order the website
                    uses.
        Returns:
            CategoriesDict - OrderedDict - ordered dict of ( category, category_url_path )
        '''
        MainPage = requests.get(SITE['root'])
        MainPageXML = get_xml(MainPage.text)
        Categories = MainPageXML.xpath('//div[contains(@class,"category")]/ul/li/a/text()')
        URLs = MainPageXML.xpath('//div[contains(@class,"category")]/ul/li/a/@href')
        CategoriesList = list(zip(Categories, URLs))
        CategoriesDict = OrderedDict( CategoriesList )
        return CategoriesDict

    @property
    def categories(self):
        '''
        Purpose;    Get an ordered list of all available categories.
        '''
        if self._categories == None:
            self._categories = self._getCategories()
        return list( self._categories.keys() )

    @staticmethod
    def _extractTopicsFromSearchResult( SearchResultXML ):
        '''
        Purpose:    Extract topics on a search result xml page.
        Arguments:
            SearchResultXML - xml page - xml page returned in search
        Returns:
            TopicsDict - dict - dictionary of topics extracted from page.
        '''
        TopicsElms = SearchResultXML.xpath('//div[@class="nbx"]/script/text()')
        if len( TopicsElms ) == 0:
            return {}
        else:
            TopicsElm = TopicsElms[0]
            TopicDicts = eval(re.search(r'var cloudTopics = (.*?);', TopicsElm).group(1))
            TopicsDict = dict( [ tuple( x.values() ) for x in TopicDicts ] )
            return TopicsDict

    def _calculateConfidences( self, Abbs ):
        '''
        Purpose:    Calculate confidence for list of abbreviations.
        Arguments:
            Abbs - list of Abbreviations - abbreviations to calculate confidence for
        Returns:
            Abbs - list of Abbreviations - same list of abbreviations with confidences calculated
        '''

        # ADJUST RATINGS IF MIN RATING LESS THAN 0 - need to shift all ratings to make them positive, without changing relative weight
        Ratings = [ x.rating for x in Abbs ]
        if len( Ratings ) > 0:
            RatingMin = min( Ratings )
            if RatingMin < 0:
                for i in range( len( Ratings ) ):
                    Ratings[i] += abs( RatingMin ) + 1                                          # add 1, because can't have rating of zero
            RatingSum = sum( Ratings )

            # CALCULATE CONFIDENCE
            for i, a in enumerate(Abbs):
                Abbs[i] = Abbs[i]._replace(
                    confidence=Ratings[i] / RatingSum)
        return Abbs

    def _extractAbbreviations( self, SearchResultXML, CalculateConfidence=True ):
        '''
        Purpose:    Extract abbreviations from page xml allacronyms.com page.
        Arguments:
            SearchResultXML - xml page - xml page returned in search
            CalculateConfidence - bool - True if you want to calculate confidence in
                                            each abbreviation as the ratio of each rating
                                            to sum of all abbreviations' ratings on page.
                                            Ratings are temporarily normalized before
                                            calculating to account for negative ratings.
                                            The actual ratings are not altered.
        Returns:
            Abbreviations - list of Abbreviation - list of all abbreviations extracted.
        '''
        AbbrevElms = SearchResultXML.xpath('//div[@class="rows items_content"]/ul[1]/li')   # 1 is the actual results, 2 is RELATED
        Abbreviations = []
        for AbbrevElm in AbbrevElms:
            Rating = int(AbbrevElm.xpath('.//div[@class="n"]/text()')[0])
            AbbElms = AbbrevElm.xpath('.//div[@class="pairAbb"]/a/text()')
            if len( AbbElms ) > 0:                                                          # form 1 of abbreviations on site
                Abb = AbbElms[0]
                Def = AbbrevElm.xpath('.//div[@class="pairDef"]/text()')[0].strip()
            else:                                                                           # form 2 of abbreviations on site
                Abb = AbbrevElm.xpath( './/div[@class="pairDef"]/a/text()' )[0]
                Def = AbbrevElm.xpath( './/div[@class="pairDef"]/text()' )[0].strip()
            abbreviation = Abbreviation( rating=Rating, abb=Abb, definition=Def, confidence=None )
            Abbreviations.append( abbreviation )
        if CalculateConfidence:                                                             # calculative confidence based on weight of rating to sum of all ratings on page
            Abbreviations = self._calculateConfidences( Abbreviations )
        return Abbreviations

    def _getTopics( self, Keywords=None, Category=None ):
        '''
        Purpose:    Get topics for keywords and/or categories.
        Arguments:
            Keywords - str - keywords to filter topics ( abbreviation / words that could be abbreviation )
            Category - str - category to search for topics under
        Returns:
            TopicsDict - dict - dictionary of topic : topic_url
                                topic_url could be used to further filter the abbreviation results
                                or be used to get a page containing abbreviations for the topic
        '''

        # VALIDATE USER INPUT
        if Category != None and not Category in self.categories:
            return []

        TopicsDict = {}

        # GET TOPICS JUST FOR CATEGORY
        if Keywords == None and Category != None:                                   # handle case where just category provided to filter topics
            if Category in self.categories:

                # BUILD TOPICS PAGE URL
                if 'any' in Category.lower():                                       # handle case where no category selected
                    TopicPageURL = SITE['root'] + SITE['top_topics']
                else:                                                               # handle case where any other category selected
                    TopicPageURL = SITE['root'] + self._categories[ Category ] + \
                                   SITE['top_topics']

                # PARSE TOPICS ON PAGE
                TopicResponse = requests.get(TopicPageURL)
                TopicResultXML = get_xml(TopicResponse)
                Topics = \
                    TopicResultXML.xpath( '//div[@class="popular"]/ul/li/a/text()' )
                TopicURLs = \
                    TopicResultXML.xpath( '//div[@class="popular"]/ul/li/a/@href' )
                TopicsDict = dict( zip( Topics, TopicURLs ) )

        # GET TOPICS FOR KEYWORDS
        elif Keywords != None:

            # BUILD TOPICS PAGE URL
            TopicPageURL = SITE['root']
            if Category != None and Category in self.categories and \
                not 'any' in Category.lower():                                      # handle case where no category selected
                TopicPageURL += '/' + self._categories[ Category ]
            TopicPageURL += '/' + Keywords

            # PARSE TOPICS ON PAGE
            TopicResponse = requests.get( TopicPageURL )
            TopicResultXML = get_xml( TopicResponse.text )
            TopicsDict = self._extractTopicsFromSearchResult( TopicResultXML )

        return TopicsDict

    def getTopics( self, Keywords=None, Category=None ):
        '''
        Purpose:    Get a list of topics for a set of Keywords and/or Category.
        Arguments:
            Keywords - str - keywords to filter topics ( abbreviation / words that could be abbreviation )
            Category - str - category to search for topics under
        Returns:
            TopicsList - list of str - list of topics for query
        '''
        TopicsList = self._getTopics( Keywords, Category ).keys()
        return TopicsList

    def _search( self, Keywords, Category=None, Topic=None, TopCount=1 ):
        '''
        Purpose:    Search the site with the given set of search criteria.
        Arguments:
            Keywords - str - str of keywords to search under. Can be abbreviation
                                or definition
            Category - str - category to search under
            Topic - str - topic to search under
            TopCount - int - number of results to return
        Returns:
            Abbs - list of Abbreviations - Abbreviations returned from search.
        '''

        Abbs = []

        # VALIDATE USER INPUTS
        if Keywords == None:
            raise ValueError( 'ERROR : KEYWORDS CANNOT BE NONE' )
        elif not isinstance( Keywords, str ):
            raise ValueError( 'ERROR : KEYWORDS MUST BE A STRING' )
        if Category != None and not Category in self.categories:
            return []

        # IF NOT DEFINITION, LET THE SITE FIGURE OUT IF DEF OR ABB GIVEN
        # BUILD API URL FOR QUERY / VALIDATE - site automatically detects if abb or def given
        # and generates the url based on this, if this GET request is used
        if Category == None:
            iCategory = 0
        else:
            iCategory = list( self._categories.keys() ).index( Category )
        SearchURL = SITE['root'] + SITE['search']. \
                    format(keywords=Keywords
                           , icategory=iCategory)

        # INITIAL SEARCH
        SearchResponse = requests.get( SearchURL )
        if SearchResponse.status_code != 200:                               # error return no results
            return []
        SearchResultXML = get_xml(SearchResponse.text)

        # IF TOPIC PROVIDED, FIND TOPIC URL FROM INITIAL SEARCH AND GET REFINED SEARCH WITH TOPIC
        if Topic != None:
            TopicsDict = self._extractTopicsFromSearchResult(SearchResultXML)
            if not Topic in TopicsDict:                                     # if topic not found for search, return empty results
                return []
            SearchURL = SearchResponse.url + '/' + TopicsDict[ Topic ]
            SearchResponse = requests.get( SearchURL )
            SearchResultXML = get_xml( SearchResponse.text )

        # GET ABBREVIATIONS UNTIL TOPCOUNT MET OR SEARCH RESULTS END
        Abbs += self._extractAbbreviations( SearchResultXML )
        if len( Abbs ) < TopCount:
            PageCountElms = SearchResultXML.xpath(
                                    '//div[@class="aa-pagination"]' +
                                    '/a[contains(@class,"counter")]' +
                                    '/text()' )
            if len( PageCountElms ) > 0:
                PageCount = int(PageCountElms[0].rsplit('/')[1])
                Search_Base_URL = SearchResponse.url
                iPage = 2
                while len( Abbs ) < TopCount and \
                    iPage < PageCount:
                    Next_Search_URL = Search_Base_URL + '/' + str(iPage)
                    NextSearchResponse = requests.get( Next_Search_URL )
                    NextSearchXML = get_xml( NextSearchResponse.text )
                    Abbs += self._extractAbbreviations( NextSearchXML, False )
                    iPage += 1
                Abbs = self._calculateConfidences( Abbs )

        return Abbs

    def search( self, Keywords, Category=None, Topic=None, Quantity=1 ):
        '''
        Purpose:    Get abbreviations / definitions / ratings for a string
                    you think may have an abbreviation.
        Arguments:
            Keywords - str - combination of keywords you think might have an abbreviation
            Category - str - [ optional ] category to search under
            Quantity - int - [ optional ] how many Abbreviations to return
        Returns
            Abbs - Abbreviation or
                   list of Abbreviations -    if Quantity = 1, Abbreviation
                                              if Quantity > 1, [ Abbreviation1, Abbreviation2, ... ]
                                              if no abbreviations found,
                                                 if Quantity = 1, return None
                                                 if Quantity > 1, return []
        '''
        Abbs = self._search( Keywords=Keywords, Category=Category
                             ,Topic=Topic, TopCount=Quantity )
        if len( Abbs ) == 0:
            if Quantity == 1:
                return None
            else:
                return []
        else:
            if Quantity == 1:
                return Abbs[ 0 ]
            else:
                return Abbs[:Quantity]

    def getRandom( self ):
        '''
        Purpose:    Get random abbreviations.
        '''
        RandomURL = SITE['root'] + SITE['random']
        RandomResponse = requests.get( RandomURL )
        RandomResultXML = get_xml( RandomResponse.text )
        Abbs = self._extractAbbreviations( RandomResultXML )
        return Abbs





#!/usr/bin/python3

from collections import defaultdict
from datetime import datetime
import codecs
import json
import os
import sys

startTime = datetime.now()

KNOWN_DUPS = [ ( 't1i',   '500d' ), \
               ( 't2i',   '550d' ), \
               ( 'tl240', 'st5000' ) ]

# Class for a Product
class Product( object ):
    # using slots so we don't have to do a map lookup each time we access which will be often
    __slots__ = [ 'manu', 'model', 'modelStripped', 'family', 'name', 'listings' ]

    def __init__( self, line ):
        if line is not None:
            product_dict        = json.loads( line.lower().rstrip('\n') ) 
    
            self.name           = product_dict['product_name']
            self.manu           = product_dict['manufacturer']
            self.model          = product_dict['model']
            self.family         = product_dict['family'] if 'family' in product_dict else None
            self.modelStripped  = self.model.translate( { ord(c): None for c in '-_ ' } )
        self.listings       = []

    def prnt( self ):
        print( self.manu, '...', self.family, '...', self.model, '...', self.name )


# Class for a Listing
class Listing( object ):
    __slots__ = [ 'manu', 'title', 'jsonText' ]

    def __init__( self, line ):
        listing_dict  = json.loads( line.lower().rstrip('\n') )

        self.jsonText = line.rstrip('\n') # kept for easy output to file
        self.manu     = listing_dict[u'manufacturer']
        self.title    = listing_dict[u'title']

    def prnt( self ):
        print( self.title )


def findProductByModelByLinearSearch( title, productList, doPrint, foundProducts ):
    # searching the title for the model with '-_ ' stripped from it
    titleStripped = title.translate( { ord(c): None for c in '-_,;' } )
    for product in productList:
        # exclude anything that is a single character, these will be caught below in the token-based search
        if len( product.modelStripped ) > 1: 
            findIndex = titleStripped.find( product.modelStripped )
            if findIndex is not -1:
                isDigits    = product.modelStripped.isdigit()
                endIndex    = findIndex + len( product.modelStripped )
                beforeOne   = titleStripped[findIndex - 1] if findIndex >= 1 else '@'
                afterOne    = titleStripped[endIndex]      if len( titleStripped ) > endIndex else '@'
                afterTwo    = titleStripped[endIndex + 1]  if len( titleStripped ) > endIndex + 1 else '@'
                afterThree  = titleStripped[endIndex + 2]  if len( titleStripped ) > endIndex + 2 else '@'

                found = True
                if afterOne.isdigit() or beforeOne.isdigit():
                    found = False
                elif afterOne == 'm' and afterTwo == 'm':
                    found = False
                elif afterOne == ' ' and afterTwo == 'm' and afterThree == 'm':
                    found = False
                elif afterOne == ' ' and afterTwo == 'v' and afterThree == 'r':
                    found = False
                elif product.modelStripped == 'g1' and beforeOne == 'b':
                    found = False
                elif isDigits and ( product.manu != 'olympus' or beforeOne == 'c' ) \
                     and titleStripped.find( product.family ) == -1:
                    found = False
                
                if found:
                    foundProducts[product.name] = product
                    if doPrint:
                        product.prnt()
                        print( title )
                        print()


def findProductByModelByTokenSearch( title, productList, replaceWithSpaces, doPrint, foundProducts ):
    titleForFamilySearch = title.translate( { ord(c): None for c in '-_,;' } )
    title = title.translate( { ord(c): None for c in ';,' } ) 
    if replaceWithSpaces:
        title = title.replace( '-', ' ' ).replace( '_', ' ' )
    titleTokens = title.split()
    numTitleTokens = len( titleTokens )
    for product in productList:
        found = False
        for startTokenIndex in range( numTitleTokens ):
            word = ''
            for offset in range( 4 ):
                titleTokenIndex = startTokenIndex + offset
                if titleTokenIndex < numTitleTokens:
                    word += titleTokens[titleTokenIndex]
                    if not product.modelStripped.startswith( word ):
                        break # short-circuit
                    if word == product.modelStripped:
                        if titleTokenIndex + 1 < numTitleTokens \
                           and ( titleTokens[titleTokenIndex + 1] == 'mm' \
                                 or titleTokens[titleTokenIndex + 1] == 'vr' ):
                            pass
                        elif product.modelStripped.isdigit() and product.manu != 'olympus' \
                             and titleForFamilySearch.find( product.family ) == -1:
                            pass
                        else:
                            found = True
                            foundProducts[product.name] = product
                            if doPrint:
                                product.prnt()
                                print( title )
                                print()
                            break
            if found:
                break 


def checkForSameModel( l, productOne, productTwo ):
    if productOne.modelStripped == productTwo.modelStripped:
        if productOne.family == productTwo.family:
            productOne.listings.append( l )
        elif l.title.find( productOne.family ) != -1:
            productOne.listings.append( l )
        elif l.title.find( productTwo.family ) != -1:
            productTwo.listings.append( l )
        return True
    return False


def checkForPartialModel( l, productOne, productTwo ):
    if productOne.modelStripped.find( productTwo.modelStripped ) != -1:
        productOne.listings.append( l )
        return True
    elif productTwo.modelStripped.find( productOne.modelStripped ) != -1:
        productTwo.listings.append( l )
        return True
    return False


def checkForKnownDuplicates( l, productOne, productTwo ):
    for dupe in KNOWN_DUPS:
        if productOne.model == dupe[0] and productTwo.model == dupe[1]:
            productOne.listings.append( l )
            return True
        elif productOne.model == dupe[1] and productTwo.model == dupe[0]:
            productTwo.listings.append( l )
            return True
    return False


def addOnlyProductToListingFromMap( l, foundProducts ):
    for _, product in foundProducts.items():
        product.listings.append( l )


def findProductByModel( l, productList, doPrint ):
    foundProducts = {}

    findProductByModelByLinearSearch( l.title, productList, doPrint, foundProducts )
    findProductByModelByTokenSearch( l.title, productList, True, doPrint, foundProducts )    

    if len( foundProducts ) == 1:
        addOnlyProductToListingFromMap( l, foundProducts )
    else:
        start = l.title.find( '(' )
        end   = l.title.find( ')' )
        if start != -1 and end != -1:
            strippedTitle = l.title[:start] + l.title[end + 1:]
            products = [ product for _, product in foundProducts.items() ]
            foundProducts = {}
            findProductByModelByLinearSearch( strippedTitle, productList, doPrint, foundProducts )
            findProductByModelByTokenSearch( strippedTitle, productList, True, doPrint, foundProducts )    
        if len( foundProducts ) == 1:
            addOnlyProductToListingFromMap( l, foundProducts )
        elif len( foundProducts ) > 2:
            pass # just return... very likely a multiple product listing
        elif len( foundProducts ) > 1:
            products = [ product for _, product in foundProducts.items() ]
            if checkForSameModel( l, products[0], products[1] ) or \
               checkForPartialModel( l, products[0], products[1] ) or \
               checkForKnownDuplicates( l, products[0], products[1] ):
                pass # listing added to product in method
            else: 
                l.prnt()
                products[0].prnt();
                products[1].prnt();
                print()
                # foundProducts = {}
                # findProductByModelByTokenSearch( l.title, products, False, doPrint, foundProducts )    
                if len( foundProducts ) == 1:
                    addOnlyProductToListingFromMap( l, foundProducts )


def searchListingForProducts( l, productsByManu, productsByFamily ):
    found = False
    if not found:
        for prod_manu in productsByManu.keys():
            if l.manu.find( prod_manu ) != -1:
                found = True
                findProductByModel( l, productsByManu[ prod_manu ], False )
                break
    if not found:
        prod_manu_hit = None
        prod_manu_hit_count = 0
        for prod_manu in productsByManu.keys():    
            if l.title.find( prod_manu ) != -1:
                prod_manu_hit_count += 1
                prod_manu_hit = prod_manu
                if prod_manu_hit_count > 1:
                    break
        if prod_manu_hit_count >= 1:
            found = True
        if prod_manu_hit_count == 1:
            findProductByModel( l, productsByManu[ prod_manu_hit ], False )
    if not found:
        productFound = False
        for prodFamily in productsByFamily.keys():
            if l.title.find( prodFamily ) != -1:
                found = True
                if findProductByModel( l, productsByFamily[ prodFamily ], False ):
                    productFound = True
                    break


####### Starting the main script #######

# Pull the file paths from the command line or use default, ensure they exist
productsFileName = str( sys.argv[1] ) if len( sys.argv ) > 1 else 'input/products.txt'
if not os.path.isfile( productsFileName ):
    print( "ERROR: products file does not exist" )
    exit()

listingsFileName = str( sys.argv[2] ) if len( sys.argv ) > 2 else 'input/listings.txt'    
if not os.path.isfile( listingsFileName ):
    print( "ERROR: listings file does not exist" )    
    exit()

# Load from the listing file
with open( listingsFileName, encoding='utf-8' ) as f:
    listings = [ Listing( line ) for line in f ]

# Load from the products file
# Create some structures to separate the products by manufacturer and family
outputProducts = []
productsByManu = defaultdict( list )
productsByFamily = defaultdict( list )
with open( productsFileName, encoding='utf-8' ) as f:
    for line in f:
        product = Product( line )
        # Skip adding a couple products to the lists used are for search 
        # as they don't have enough information to reliably use
        if product.manu == 'leica' and product.family is None and product.model == 'digilux':
            outputProducts.append( product )
        elif product.manu == 'leica' and product.family == 'digilux' and product.model == 'zoom':
            outputProducts.append( product )
        else:
            outputProducts.append( product )
            for word in product.manu.split():
                productsByManu[ word ].append( product )
            if product.family is not None:
                productsByFamily[ product.family ].append( product )

# Add some fake products, this helps to remove listings 
# for multiple products of which we only have one.
# NOTE: it is not added to the outputProducts list
product = Product( None );
product.name           = 'canon_ixus_220'
product.manu           = 'canon'
product.model          = '220'
product.family         = 'ixus'
product.modelStripped  = '220'
productsByManu[ product.manu ].append( product )
productsByFamily[ product.family ].append( product )

# This is our main loop through the listings
for l in listings:
    searchListingForProducts( l, productsByManu, productsByFamily )

matchCount = 0
for p in outputProducts:
    matchCount += len( p.listings )
    # p.prnt()
    # for l in p.listings:
    #     l.prnt()
    #  print()
print( "Match Count: ", matchCount )

# Clear the result file and write out the results
outputDirectory = 'output'
if not os.path.exists( outputDirectory ):
    os.makedirs( outputDirectory )
outputFile = outputDirectory + '/results.txt'
if os.path.isfile( outputFile ):
    os.remove( outputFile )

fh = codecs.open( outputFile, 'a', 'utf-8' )
for p in outputProducts:
    listings = ', '.join( [ l.jsonText for l in p.listings ] )
    fh.write( '{ "product_name": "' + p.name + '", "listings": [ ' + listings + ' ] }\n' )
fh.close()

print( 'Time: ', datetime.now() - startTime )





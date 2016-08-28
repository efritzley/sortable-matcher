#!/usr/bin/python3

from collections import defaultdict
from datetime import datetime
import codecs
import json
import os
import sys

startTime = datetime.now()

# Class for a Product
class Product( object ):
    # using slots so we don't have to do a map lookup each time we access which will be often
    __slots__ = [ 'manu', 'model', 'modelStripped', 'family', 'name', 'listings' ]

    def __init__( self, line ):
        product_dict        = json.loads( line.lower().rstrip('\n') ) 

        self.name           = product_dict['product_name']
        self.manu           = product_dict['manufacturer']
        self.model          = product_dict['model']
        self.family         = product_dict['family'] if 'family' in product_dict else None
        self.modelStripped  = self.model.translate( { ord(c): None for c in '-_ ' } )
        self.listings       = []

    def prnt( self ):
        print( self.manu, '...', self.family, '...', self.model )

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

# Pull the file paths from the command line or use default, ensure they exist
productsFileName = str( sys.argv[1] ) if len( sys.argv ) > 1 else 'input/products.txt'
if not os.path.isfile( productsFileName ):
    print( "products file does not exist" )

listingsFileName = str( sys.argv[2] ) if len( sys.argv ) > 2 else 'input/listings.txt'    
if not os.path.isfile( listingsFileName ):
    print( "listings file does not exist" )    

# Load from the products file
# Create some structures to separate the products by manufacturer and family
products = []
products_by_manu = defaultdict( list )
products_by_family = defaultdict( list )
for line in open( productsFileName, encoding='utf-8' ):
    product = Product( line )
    products.append( product )
    products_by_manu[ product.manu ].append( product )
    if product.family is not None:
        products_by_family[ product.family ].append( product )

# Load from the listing file
listings = [ Listing( line ) for line in open( listingsFileName, encoding='utf-8' ) ]

def findProductByModel( l, productList, doPrint ):
    found = False

    # searching the title for the model with '-_ ' stripped from it
    if not found:
        titleStripped = l.title.translate( { ord(c): None for c in '-_,;' } )
        for product in productList:
            # exclude anything that is a single character, these will be caught below in the token-based search
            if len( product.modelStripped ) > 1: 
                findIndex = titleStripped.find( product.modelStripped )
                if findIndex is not -1:
                    isDigits  = product.modelStripped.isdigit()
                    endIndex  = findIndex + len( product.modelStripped )
                    beforeOne = titleStripped[findIndex - 1] if findIndex >= 1 else '@'
                    afterOne  = titleStripped[endIndex]      if len( titleStripped ) > endIndex else '@'
                    afterTwo  = titleStripped[endIndex + 1]  if len( titleStripped ) > endIndex + 1 else '@'

                    found = True
                    if afterOne.isdigit() or beforeOne.isdigit():
                        found = False
                    elif afterOne == 'm' and afterTwo == 'm':
                        found = False
                    elif isDigits and product.manu == 'canon' and titleStripped.find( product.family ) == -1:
                        found = False
                    elif product.modelStripped == 'g1' and beforeOne == 'b':
                        found = False
                    
                    if found:
                        product.listings.append( l )
                        if doPrint:
                            product.prnt()
                            l.prnt()
                            print()
                        break
    if not found:
        title = l.title.translate( { ord(c): None for c in ';,' } ) 
        titleTokens = title.replace( '-', ' ' ).replace( '_', ' ' ).split()
        numTitleTokens = len( titleTokens )
        for product in productList:
            for startTokenIndex in range( numTitleTokens ):
                word = ''
                for offset in range( 4 ):
                    if ( startTokenIndex + offset ) < numTitleTokens:
                        word += titleTokens[startTokenIndex + offset]
                        if not product.modelStripped.startswith( word ):
                            break;
                        if word == product.modelStripped:
                            product.listings.append( l )
                            found = True
                            if doPrint:
                                product.prnt()
                                l.prnt()
                                print()
                            break
                if found:
                    break
            if found:
                break
    return found

count = 0
count2 = 0
count3 = 0
notFoundCount = 0
notFoundCount2 = 0
notFoundCount3 = 0

for l in listings:
    found = False
    skip = False
    if not found:
        for prod_manu in products_by_manu.keys():
            if l.manu.find( prod_manu ) is not -1:
                count += 1
                found = True
                if not findProductByModel( l, products_by_manu[ prod_manu ], False ):
                    notFoundCount += 1
                break
    if not found:
        prod_manu_hit = None
        prod_manu_hit_count = 0
        for prod_manu in products_by_manu.keys():    
            if l.title.find( prod_manu ) is not -1:
                prod_manu_hit_count += 1
                prod_manu_hit = prod_manu
                if( prod_manu_hit_count > 1 ):
                    break
        if prod_manu_hit_count == 1:
            count2 += 1
            found = True
            if not findProductByModel( l, products_by_manu[ prod_manu ], False ):
                notFoundCount2 +=1
        elif prod_manu_hit_count > 1:
            skip = True
    if not found and not skip:
        for prod_family in products_by_family.keys():
            if l.title.find( prod_family ) is not -1:
                count3 += 1
                found = True
                if not findProductByModel( l, products_by_family[ prod_family ], False ):
                    notFoundCount3 +=1
                break
    
for p in products:
    p.prnt()
    for l in p.listings:
        l.prnt()
    print()

outputDirectory = 'output'
if not os.path.exists( outputDirectory ):
    os.makedirs( outputDirectory )
outputFile = outputDirectory + '/results.txt'
if os.path.isfile( outputFile ):
    os.remove( outputFile )

fh = codecs.open( outputFile, 'a', 'utf-8' )
for p in products:
    listingsTextList = [ l.jsonText for l in p.listings ]
    listings = ', '.join( listingsTextList )
    line = '{ "product_name": "' + p.name + '", "listings": [ ' + listings + ' ] }'
    fh.write( line + '\n' )
fh.close()

print( "the count is ", count, count2, count3, notFoundCount, notFoundCount2, notFoundCount3 )
print( 'Time: ', datetime.now() - startTime )





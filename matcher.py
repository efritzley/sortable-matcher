#!/usr/bin/python
from __future__ import print_function

from collections import defaultdict
from datetime import datetime
import json
import os
import sys

startTime = datetime.now()

reload(sys)  
sys.setdefaultencoding('utf8')

productsFileName = str( sys.argv[1] ) if len( sys.argv ) > 1 else 'input/products.txt'
if not os.path.isfile( productsFileName ):
    print( "products file does not exist" )

listingsFileName = str( sys.argv[2] ) if len( sys.argv ) > 2 else 'input/listings.txt'    
if not os.path.isfile( listingsFileName ):
    print( "listings file does not exist" )    

class Product( object ):
    __slots__ = [ 'manu', 'model', 'modelStripped', 'family', 'name', 'listings' ]

    def __init__( self, line ):
        product_dict        = json.loads( line.lower().rstrip('\n') )
        self.name           = product_dict[u'product_name']
        self.manu           = product_dict[u'manufacturer']
        self.model          = product_dict[u'model']
        self.family         = product_dict[u'family'] if u'family' in product_dict else None
        self.modelStripped  = self.model.encode('ascii','ignore').translate( None, '-_ ' )
        self.listings       = []

    def prnt( self ):
        print( self.manu, '...', self.family, '...', self.model )

class Listing( object ):
    __slots__ = [ 'manu', 'title', 'jsonText' ]

    def __init__( self, line ):
        self.jsonText = line.rstrip('\n')
        listing_dict  = json.loads( line.lower().rstrip('\n') )
        self.manu     = listing_dict[u'manufacturer']
        self.title    = listing_dict[u'title']

    def prnt( self ):
        print( self.title )


products = []
products_by_manu = defaultdict( list )
products_by_family = defaultdict( list )
for line in open( productsFileName ):
    product = Product( line )
    products.append( product )
    products_by_manu[ product.manu ].append( product )
    if product.family is not None:
        products_by_family[ product.family ].append( product )

listings = [ Listing( line ) for line in open( listingsFileName ) ]

# for manu in products_by_manu.keys():
#     print manu, len( products_by_manu_by_family[ manu ] ) 
#     for family in products_by_manu_by_family[ manu ].keys():
#         print manu, family

# for p in products:
#     print p.model;

def findProductByModel( l, productList, doPrint ):
    found = False
    if not found:
        titleStripped = l.title.encode( 'ascii', 'ignore' ).translate( None, '-_,;' )
        for product in productList:
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
        title = l.title.encode( 'ascii', 'ignore' ).translate( None, ';,' )
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


    # if not found:
    #     for product in productList:
    #         findIndex = l.title.find( product.model )
    #         if findIndex is not -1:
    #             if len( l.title ) <= findIndex + len( product.model ) or \
    #                not l.title[findIndex + len(product.model)].isnumeric():
    #                 product.listings.append( l )
    #                 product.prnt()
    #                 l.prnt()
    #                 print
    #                 found = True
    #                 break;
    # if not found:
    #     for product in productList:
    #         if l.title.find( product.model ) is not -1:
    #             product.listings.append( l )
    #             product.prnt()
    #             l.prnt()
    #             print
    #             found = True
    #             break;
    # if not found:
    #     # TODO: can the above be reused?
    #     titleStripped = l.title.encode('ascii','ignore').translate( None, '-_' )
    #     for product in productList:
    #         if titleStripped.find( product.modelStrippedL2 ) is not -1:
    #             product.listings.append( l )
    #             product.prnt()
    #             l.prnt()
    #             print
    #             found = True
    #             break
    # if not found:
    #     # TODO: can the above be reused?
    #     titleTokens = l.title.encode('ascii','ignore').translate( None, '-_;' ).split()
    #     numTitleTokens = len( titleTokens )
    #     for product in productList:
    #         if not found:
    #             for i in range( 0, numTitleTokens - 1 ):
    #                 word = titleTokens[i] + titleTokens[i+1]
    #                 if word == product.modelStrippedL2:
    #                     product.listings.append( l )
    #                     # print "TWO WORD"
    #                     # product.prnt()
    #                     # l.prnt()
    #                     # print
    #                     found = True
    #                     break
    #                 if product.manu == 'sony' and \
    #                    word[:-1] == product.modelStrippedL2 and \
    #                    word[-1:].isalpha():
    #                     product.listings.append( l )
    #                     # print "TWO WORD"
    #                     # product.prnt()
    #                     # l.prnt()
    #                     # print
    #                     found = True
    #                     break
    #         if not found:
    #             for i in range( 0, numTitleTokens - 2 ):
    #                 word = titleTokens[i] + titleTokens[i+1] + titleTokens[i+2]
    #                 if word == product.modelStrippedL2:
    #                     product.listings.append( l )
    #                     # print "THREE WORD"
    #                     # product.prnt()
    #                     # l.prnt()
    #                     # print
    #                     found = True
    #                     break
    # if not found:
    #     # TODO: can the above be reused?
    #     titleStripped = l.title.encode('ascii','ignore').translate( None, '-_ ' )
    #     for product in productList:
    #         if titleStripped.find( product.modelStrippedL2 ) is not -1:
    #             product.listings.append( l )
    #             # if product.manu == 'sony':
    #             product.prnt()
    #             l.prnt()
    #             print
    #             found = True
    #             break
    return found

count = 0
count2 = 0
count3 = 0
notFoundCount = 0
notFoundCount2 = 0
notFoundCount3 = 0

# print 'Models'
# for p in products:
#     print p.model
# print

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
    
# for p in products:
#     p.prnt()
#     for l in p.listings:
#         l.prnt()
#     print()

outputDirectory = 'output'
if not os.path.exists( outputDirectory ):
    os.makedirs( outputDirectory )
outputFile = outputDirectory + '/results.txt'
if os.path.isfile( outputFile ):
    os.remove( outputFile )

fh = open( outputFile, 'a')
for p in products:
    listingsTextList = [ l.jsonText for l in p.listings ]
    listings = ', '.join( listingsTextList )
    line = '{ "product_name": "' + p.name + '", "listings": [ ' + listings + ' ] }'
    fh.write( line + '\n' )
fh.close()

print( "the count is ", count, count2, count3, notFoundCount, notFoundCount2, notFoundCount3 )
print( 'Time: ', datetime.now() - startTime )





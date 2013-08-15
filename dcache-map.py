#!/usr/bin/env python
#
#
import ldap
import sys
import cgi


def toHostNames(site):
  dn, attrs = site
  return attrs['GlueSEUniqueID'][0], \
    attrs['GlueSEImplementationVersion'][0], \
    attrs['GlueSETotalOnlineSize'][0], \
    attrs['GlueSEUsedOnlineSize'][0], \
    attrs['GlueForeignKey'][0]

def skipBad(site):
 dn, attrs = site
 return attrs.has_key('GlueSETotalOnlineSize')

def getSiteInfo(con, site):
  filter_f = '(%s)' % site
  attrs = ['GlueSiteLongitude','GlueSiteLatitude', 'GlueSiteDescription','GlueSiteLocation', 'GlueSiteWeb']
  infos = con.search_s( base_dn, ldap.SCOPE_SUBTREE, filter_f, attrs )
  for dn, info in infos:
    m = {}
    m['latitude'] = float(info['GlueSiteLatitude'][0])
    m['longitude'] = float(info['GlueSiteLongitude'][0])
    m['desc'] = cgi.escape(info['GlueSiteDescription'][0], True)
    m['location'] = info['GlueSiteLocation'][0]
    m['url'] = info['GlueSiteWeb'][0]
    return m
 

con = ldap.initialize('ldap://lcg-bdii.cern.ch:2170')
base_dn = 'o=grid'
filter_s = '(&(objectClass=GlueSE)(GlueSEImplementationName=dCache))'
attrs = ['GlueSEUniqueID','GlueSEImplementationVersion', 'GlueSETotalOnlineSize', 'GlueSEUsedOnlineSize', 'GlueForeignKey']

sites = con.search_s( base_dn, ldap.SCOPE_SUBTREE, filter_s, attrs )

#
ses = map(toHostNames, filter( skipBad, sites))

print "var markers = ["

for se in ses:
  host, version, size, used, id = se
  gr = getSiteInfo(con, id)

  try:
    location = ('{ lat: %f, lng: %f, name: "%s", version: "%s", size: "%s", used:  "%s", desc: "%s", loc: "%s", url: "%s" },') % \
                 ( gr['latitude'], gr['longitude'], host, version, size, used, gr['desc'], gr['location'], gr['url'])
    print location
  except:
    pass
  
print "]"

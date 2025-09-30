#!/usr/bin/env python
#
#
import ldap
import sys
import json
import time
import requests


COLLECTOR_URL = 'https://stats.dcache.org/collector'


# Some sites to exclude from publishing as they publish vie telemetry service
sites_to_exclude = [
  "DESY-ZN",
  "IN2P3-CC",
  "IN2P3-LAPP",
  "pic",
  "BEgrid-ULB-VUB"
]

def toHostNames(site):
  dn, attrs = site
  return attrs['GlueSEUniqueID'][0], \
    attrs['GlueSEImplementationVersion'][0], \
    attrs['GlueSETotalOnlineSize'][0], \
    attrs['GlueSEUsedOnlineSize'][0], \
    attrs['GlueForeignKey'][0]

def skipBad(site):
 dn, attrs = site
 return 'GlueSETotalOnlineSize' in attrs

def getSiteInfo(con, site):
  filter_f = '(%s)' % site.decode("utf-8")
  attrs = ['GlueSiteLongitude','GlueSiteLatitude', 'GlueSiteDescription','GlueSiteLocation', 'GlueSiteWeb', 'GlueSiteUniqueID']
  infos = con.search_s( base_dn, ldap.SCOPE_SUBTREE, filter_f, attrs )
  for dn, info in infos:
    m = {}
    m['latitude'] = float(info['GlueSiteLatitude'][0])
    m['longitude'] = float(info['GlueSiteLongitude'][0])
    m['desc'] = info['GlueSiteUniqueID'][0]
    m['location'] = info['GlueSiteLocation'][0]
    m['url'] = info['GlueSiteWeb'][0]
    return m
 

con = ldap.initialize('ldap://lcg-bdii.egi.eu:2170')
base_dn = 'o=grid'
filter_s = '(&(objectClass=GlueSE)(GlueSEImplementationName=dCache))'
attrs = ['GlueSEUniqueID','GlueSEImplementationVersion', 'GlueSETotalOnlineSize', 'GlueSEUsedOnlineSize', 'GlueForeignKey']

sites = con.search_s( base_dn, ldap.SCOPE_SUBTREE, filter_s, attrs )

#
ses = map(toHostNames, filter( skipBad, sites))


for se in ses:
  host, version, size, used, id = se
  gr = getSiteInfo(con, id)

  if gr is None:
    continue

  if gr['desc'].decode("utf-8") in sites_to_exclude:
    continue

  try:

    record = {}
    record['siteName'] = gr['desc'].decode("utf-8")
    record['storage'] = int(size)*1000*1000*1000
    record['version'] = version.decode("utf-8").split()[0]
    record['location'] = {'lat': gr['latitude'], 'lon': gr['longitude']}
    record['timestamp'] = round(time.time() * 1000)

    json_data = json.dumps(record)
    print (json_data)

    res = requests.post(COLLECTOR_URL, json = record)
    print("Response: ", res.status_code, res.reason)

  except Exception as e:
    pass
  

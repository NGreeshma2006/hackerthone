import json, urllib.request
base='http://127.0.0.1:5174/api'
def get(path):
    with urllib.request.urlopen(base+path,timeout=10) as response: return json.load(response)
before=get('/products')
for language,text in [('hi','चावल कितना बचा है?'),('te','బియ్యం ఎంత ఉంది?'),('en','What should I reorder?')]:
    request=urllib.request.Request(base+'/voice/process',data=json.dumps({'language':language,'text':text}).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=10) as response:
        result=json.load(response)
        assert result['status']=='answer',result
        assert result['language']==language,result
        print(language+': query answered successfully')
after=get('/products')
assert before==after, 'A query must not change stock'
print('Live frontend proxy and backend verified; inventory unchanged.')

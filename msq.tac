import pwd

from twisted.application import internet
from twisted.application import service
from twisted.internet import reactor
from twisted.internet import threads
from twisted.web import resource
from twisted.web import server

import pymongo

def incrementUserCount(user, step=1):
    count = pymongo.Connection().msq.count
    count.update({'user': user}, {'$inc': {'count': step}}, True)

def getAllUsers():
    count = pymongo.Connection().msq.count
    return count.find()


class UpdateUser(resource.Resource):
    isLeaf = True
    
    def __init__(self, user):
        resource.Resource.__init__(self)
        self.user = user

    def render_GET(self, request):
        d = threads.deferToThread(incrementUserCount, self.user)
        d.addCallback(lambda _ : request.redirect('')).addCallback(lambda _ : request.finish())
        
        return server.NOT_DONE_YET

class ListCounts(resource.Resource):
    isLeaf = True
    
    def render_GET(self, request):
        d = threads.deferToThread(getAllUsers)

        def writeUsers(users):
            return '\n'.join(['<html>',
                              '<head>',
                              '<title>Msq</title>',
                              '</head>',
                              '<body>',
                              '<ul>',
                              '\n'.join(['<li>%s - %d</li>' % (str(u['user']), int(u['count'])) for u in users]),
                              '</ul>',
                              '</body>',
                              '</html>'])

        d.addCallback(writeUsers).addCallback(request.write).addCallback(lambda _ : request.finish())
        
        return server.NOT_DONE_YET
    
class Root(resource.Resource):
    """Root resource"""

    def getChild(self, path, request):
        if path == '':
            return ListCounts()
        elif path != 'favicon.ico':
            return UpdateUser(path)
        else:
            return resource.NoResource()

root = Root()


user = pwd.getpwnam('www-data')

application = service.Application('msq', uid=user.pw_uid, gid=user.pw_gid)
serviceCollection = service.IServiceCollection(application)
internet.TCPServer(1313, server.Site(root)).setServiceParent(serviceCollection)

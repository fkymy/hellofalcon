import falcon

from .images import Resource

# :) weee
api = application = falcon.API()

images = Resource()
api.add_route('/images', images)


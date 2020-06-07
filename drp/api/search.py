from sqlalchemy import text
from sqlalchemy.sql import func

from flask_restful import Resource

from .posts import serialize_post

from ..models import Post

from ..db import db


class PostSearchResource(Resource):

    def get(self, searched):
        """
        Gets the results of a full text search on all posts.
        ---
        parameters:
          - name: searched
            in: path
            type: string
            required: true
        responses:
          200:
            schema:
              type: array
              items:
                $ref: "#/definitions/Post"
        """
        # Construct text search query
        ts_query = func.plainto_tsquery('english', searched)
        # Compute rank for each search result
        ts_rank = func.ts_rank_cd(Post.__ts_vector__, ts_query).label("rank")
        # Query for the search results ordered by rank
        results = db.session.query(Post, ts_rank) \
            .filter(Post.__ts_vector__.op('@@')(ts_query)) \
            .order_by(text("rank desc")) \
            .all()
        return [serialize_post(result[0])
                for result in results]

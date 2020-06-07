from sqlalchemy import text
from sqlalchemy.sql import func

from flask import request
from flask_restful import Resource, abort

from .posts import serialize_post

from ..models import Post

from ..db import db


def extract_results(query):
    return [serialize_post(result[0])
            for result in query.all()]


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
          - name: page
            in: query
            type: number
            required: false
          - name: results_per_page
            in: query
            type: number
            required: false
        responses:
          200:
            schema:
              type: array
              items:
                $ref: "#/definitions/Post"
        """
        page = request.args.get("page")
        results_per_page = request.args.get("results_per_page")

        # Construct text search query
        ts_query = func.plainto_tsquery('english', searched)
        # Compute rank for each search result
        ts_rank = func.ts_rank_cd(Post.__ts_vector__, ts_query).label("rank")
        # Query for the search results ordered by rank
        query = db.session.query(Post, ts_rank) \
            .filter(Post.__ts_vector__.op('@@')(ts_query)) \
            .order_by(text("rank desc"))

        if page is None or results_per_page is None:
            return extract_results(query)

        if not page.isdigit() or not results_per_page.isdigit():
            return abort(400, message="Page and results_per_page fields must "
                         "be numbers.")

        page = int(page)
        results_per_page = int(results_per_page)

        query = query.limit(results_per_page).offset(page * results_per_page)

        return extract_results(query)

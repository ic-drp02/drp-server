from sqlalchemy import text, case
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import cast
from sqlalchemy.dialects.postgresql import TEXT

from flask import request
from flask_restful import Resource, abort

from .posts import serialize_post
from .files import serialize_file

from ..models import Post, File

from ..swag import swag

from ..db import db


@swag.definition("FileWithPost")
def serialize_file_with_post(result):
    """
    Represents a file with the associated post.
    ---
    properties:
      file:
        $ref: "#/definitions/Post"
      post:
        $ref: "#/definitions/Post"
    """
    return {
        "file": serialize_file(result[0]),
        "post": serialize_post(result[1])
    }


def construct_fulltext_query_and_rank(searched):
    # Text version of the text search query directly constructed from
    # the searched string
    simple_ts_query_text = cast(
        func.plainto_tsquery('english', searched), TEXT)
    # Text version of the search query using prefix search for the last
    # word in the base query
    # Case expression is necessary to capture the case of empty base query
    # (arising e.g. when the query consists entirely of special characters
    # and stop words)
    prefix_ts_query_text = case([
        (
            simple_ts_query_text == "",
            cast("", TEXT)
        )],
        else_=simple_ts_query_text.op('||')(cast(":*", TEXT))
    )
    # Final text search query
    ts_query = func.to_tsquery('english', prefix_ts_query_text)
    # Rank for each search result
    ts_rank = func.ts_rank_cd(Post.__ts_vector__, ts_query).label("rank")
    return (ts_query, ts_rank)


def limit_query(query, page, results_per_page):
    page = int(page)
    results_per_page = int(results_per_page)

    return query.limit(results_per_page).offset(page * results_per_page)


def extract_results_posts(query):
    return [serialize_post(result[0])
            for result in query.all()]


def extract_results_files_posts(query):
    return [serialize_file_with_post(result)
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
          - name: guidelines_only
            in: query
            type: boolean
            required: false
        responses:
          200:
            schema:
              type: array
              items:
                $ref: "#/definitions/Post"
        """
        if searched == "":
            return abort(400, message="Empty string search is invalid.")

        page = request.args.get("page")
        results_per_page = request.args.get("results_per_page")
        guidelines_only = request.args.get("guidelines_only")

        ts_query, ts_rank = construct_fulltext_query_and_rank(searched)

        # Query for the search results ordered by rank
        query = db.session.query(Post, ts_rank) \
            .filter(Post.__ts_vector__.op('@@')(ts_query))
        if guidelines_only == "true":
            query = query.filter(Post.is_guideline)
        query = query.order_by(text("rank desc"), Post.created_at.desc())

        if page is None or results_per_page is None:
            return extract_results_posts(query)

        if not page.isdigit() or not results_per_page.isdigit():
            return abort(400, message="Page and results_per_page fields must "
                         "be numbers.")

        query = limit_query(query, page, results_per_page)

        return extract_results_posts(query)


class FileSearchResource(Resource):

    def get(self, searched):
        """
        Gets the results of a full text search on posts, returning a list of
        files associated with these posts.
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
                 $ref: "#/definitions/FileWithPost"
        """
        if searched == "":
            return abort(400, message="Empty string search is invalid.")

        page = request.args.get("page")
        results_per_page = request.args.get("results_per_page")

        ts_query, ts_rank = construct_fulltext_query_and_rank(searched)

        # Rank for each search result
        ts_rank = func.ts_rank_cd(Post.__ts_vector__, ts_query).label("rank")
        # Query for the search results ordered by rank
        query = db.session.query(File, Post, ts_rank) \
            .join(File) \
            .filter(Post.__ts_vector__.op('@@')(ts_query)) \
            .order_by(text("rank desc"), File.id.desc())

        if page is None or results_per_page is None:
            return extract_results_files_posts(query)

        if not page.isdigit() or not results_per_page.isdigit():
            return abort(400, message="Page and results_per_page fields must "
                         "be numbers.")

        query = limit_query(query, page, results_per_page)

        return extract_results_files_posts(query)

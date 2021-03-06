from sqlalchemy import text, case
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import cast
from sqlalchemy.dialects.postgresql import TEXT

from flask import request
from flask_restful import Resource, abort

from .posts import serialize_post

from ..models import Post, Post_Tag, Tag

from ..db import db


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
          - name: include_old
            in: query
            type: boolean
            required: false
          - name: tag
            in: query
            type: string
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
        include_old = request.args.get("include_old")
        tag = request.args.get("tag")

        ts_query, ts_rank = construct_fulltext_query_and_rank(searched)

        # Query for the search results ordered by rank
        query = db.session.query(Post, ts_rank) \
            .filter(Post.__ts_vector__.op('@@')(ts_query))
        if (include_old != "true"):
            query = query.filter(Post.is_current)
        if guidelines_only == "true":
            query = query.filter(Post.is_guideline)
        if tag is not None:
            query = query.join(Post_Tag).join(Tag).filter(Tag.name == tag)
        query = query.order_by(text("rank desc"), Post.created_at.desc())

        if page is None or results_per_page is None:
            return extract_results_posts(query)

        if not page.isdigit() or not results_per_page.isdigit():
            return abort(400, message="Page and results_per_page fields must "
                         "be numbers.")

        query = limit_query(query, page, results_per_page)

        return extract_results_posts(query)

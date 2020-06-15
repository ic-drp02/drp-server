from flask import request
from flask_restful import Resource, abort

from sqlalchemy.exc import IntegrityError

from ..db import db
from ..models import Tag
from ..swag import swag


@swag.definition("Tag")
def serialize_tag(tag):
    """
    Represents a tag.
    ---
    properties:
      id:
        type: integer
      name:
        type: string
    """
    return {
        "id": tag.id,
        "name": tag.name
    }


class TagResource(Resource):

    def put(self, id):
        """
        Updates a single tag by id.
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
          - in: body
            name: post
            schema:
              type: object
              properties:
                name:
                  type: string
                  required: true
                  maxLength: 30
        responses:
          204:
            description: Success
          404:
            description: Not found
        """
        body = request.json

        name = body.get("name")

        tag = Tag.query.filter(Tag.id == id).one_or_none()
        if tag is None:
            return abort(404)

        if name is not None:
            if len(name) > 30:
                return abort(400, message="`name` must not be more than 30"
                             " characters.")
            tag.name = name

        try:
            db.session.commit()
        except IntegrityError as err:
            if err.orig.pgcode == "23505":
                return abort(422,
                             message="A tag with this name already exists.")
            else:
                raise

        return serialize_tag(tag)

    def delete(self, id):
        """
        Deletes a single tag by id.
        ---
        parameters:
          - name: id
            in: path
            type: integer
            required: true
        responses:
          204:
            description: Success
          404:
            description: Not found
        """
        tag = Tag.query.filter(Tag.id == id).one_or_none()

        if tag is None:
            return abort(404)

        db.session.delete(tag)
        db.session.commit()

        return '', 204


class TagListResource(Resource):

    def get(self):
        """
        Gets a list of all tags.
        ---
        responses:
          200:
            schema:
              type: array
              items:
                $ref: "#/definitions/Tag"
        """
        return [serialize_tag(tag) for tag in Tag.query.order_by(Tag.name)]

    def post(self):
        """
        Creates a new tag.
        ---
        parameters:
          - in: body
            name: post
            schema:
              type: object
              properties:
                name:
                  type: string
                  required: true
                  maxLength: 30
        responses:
          200:
            schema:
              $ref: "#/definitions/Tag"
        """
        body = request.json

        name = body.get("name")

        if name is None:
            return abort(400, message="`name` field is required.")

        if len(name) > 30:
            return abort(400, message="`name` must not be more than 30"
                         " characters.")

        tag = Tag(name=name)

        db.session.add(tag)

        try:
            db.session.commit()
        except IntegrityError as err:
            if err.orig.pgcode == "23505":
                return abort(422,
                             message="A tag with this name already exists.")
            else:
                raise

        return serialize_tag(tag)

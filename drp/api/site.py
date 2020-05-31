from flask import request
from flask_restful import Resource, abort

from sqlalchemy.exc import IntegrityError

from ..db import db
from ..models import Site
from ..swag import swag


@swag.definition("Site")
def serialize_site(site):
    """
    Represents a site.
    ---
    properties:
      id:
        type: integer
      name:
        type: string
    """
    return {
        "id": site.id,
        "name": site.name,
    }


class SiteResource(Resource):

    def delete(self, id):
        """
        Deletes a site.
        ---
        parameters:
          - in: path
            name: id
            type: integer
            required: true
        responses:
          204:
            description: Success
          404:
            description: Not found
        """
        site = Site.query.filter(Site.id == id).one_or_none()

        if site is None:
            return abort(404)

        return "", 204


class SiteListResource(Resource):

    def get(self):
        """
        Gets a list of all sites.
        ---
        responses:
          200:
            description: Success
            schema:
              $ref: "#/definitions/Site"
        """
        sites = Site.query.all()
        return [serialize_site(site) for site in sites]

    def post(self):
        """
        Creates a new site.
        ---
        paramters:
          - in: body
            name: site
            schema:
              type: object
              properties:
                name: string
                required: true
        """
        body = request.json

        name = body.get("name")

        if name is None:
            return abort(400, message="Name is required.")

        site = Site(name=name)

        db.session.add(site)

        try:
            db.session.commit()
        except IntegrityError as err:
            if err.orig.pgcode == "23505":
                return abort(422,
                             message="A site with this name already exists.")
            else:
                raise

        return serialize_site(site)

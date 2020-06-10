from flasgger import Swagger

swag = Swagger(template={
    "swagger": "2.0",
    "info": {
        "title": "NHS Guidelines API"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header"
        }
    }
})

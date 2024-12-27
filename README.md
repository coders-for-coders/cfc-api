
# This is a FastAPI application that provides a RESTful API for managing resources. 
# It uses MongoDB as the database backend through the Motor async driver.

# The application provides the following endpoints:

# GET /:
#     - Returns a simple hello world message
    
# GET /api/resources:
#     - Returns a list of all resources
#     - Can be filtered by type using query parameter
    
# GET /api/resources/{id}:
#     - Returns a single resource by ID
    
# POST /api/resources:
#     - Creates a new resource
#     - Requires resource data in request body
    
# PUT /api/resources/{id}:
#     - Updates an existing resource
#     - Requires resource data in request body
    
# DELETE /api/resources/{id}:
#     - Deletes a resource by ID

# The Resource model includes:
#     - id: Unique identifier
#     - title: Resource title
#     - content: Main content
#     - description: Brief description
#     - type: Resource type/category
#     - icon: Icon identifier

# Environment variables:
#     - MONGODB: MongoDB connection string
This project adopts a layered architecture pattern to ensure separation of concerns, scalability, and maintainability. A formal architecture is show in Figure [2](./images/layers.png). 

<p align="center">
  <img width="350" src="/images/layers.png" alt="Architecture Diagram" />
</p>

The core layers in this architecture are:

## Controller Layer

The Controller layer acts as the entry point for incoming API requests. It handles HTTP requests, validates inputs, and delegates business logic to the Service layer. The primary responsibilities include:

- Mapping API endpoints to methods.
- Validating request data.
- Returning appropriate HTTP responses.

## Service Layer

The Service layer encapsulates the business logic of the application. It acts as a bridge between the Controller and Repository layers, ensuring data consistency and applying domain-specific rules. Key tasks include:

- Coordinating operations involving multiple repositories.
- Implementing reusable business logic.
- Managing transaction boundaries.


## Repository Layer
The Repository layer is responsible for interacting with the database or persistence layer. It abstracts database queries and provides methods to fetch, save, update, or delete entities. Responsibilities include:

- Encapsulating database operations.
- Maintaining data integrity.
- Supporting various query mechanisms.


# Data flow and conversion with DTO and Models

To maintain clear separation between external and internal representations of data, this project uses Data Transfer Objects (DTOs) and Models:

## 1. Data Transfer Objects (DTOs)

DTOs are lightweight objects used to transfer data between the external world (e.g., API clients) and the application. They are tailored to match the structure of API requests and responses, ensuring:

- A simplified and consistent format for external consumers.
- Decoupling the internal domain model from API contracts.
- Easier validation of input data.

## 2. Models
Internally, the application uses domain Models, which represent the core business entities and their behaviors. Models are designed to:

- Capture the structure of data as required by the business logic.
- Include relationships and methods specific to domain operations.

## 3. Conversion
A key part of the architecture is the conversion process:

1. Incoming Data: External data received in DTO format is validated in the Controller and converted to a domain Model in the Service layer.

2. Business Logic: Operations and transformations are performed using Models.

3. Outgoing Data: The resulting data is converted back to a DTO in the Service layer before being sent to the Controller for the API response.






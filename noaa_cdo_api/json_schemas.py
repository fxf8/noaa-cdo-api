"""
JSON Schema Definitions for NOAA API Responses
==============================================

This module defines `TypedDict` structures that represent the JSON responses from the NOAA NCEI API v2. The schemas ensure type safety and provide clear documentation on the expected structure of API responses.

Each class corresponds to a specific API endpoint, describing the structure of the JSON data returned by that endpoint.

Motivations:
-----------
1. **Type Safety**:
   - Prevents runtime errors by catching type mismatches during development
   - Enables IDE autocompletion and inline documentation
   - Makes refactoring safer by identifying all affected code paths

2. **Documentation as Code**:
   - Schema definitions serve as both runtime type checking and API documentation
   - Field descriptions are always in sync with the actual implementation
   - New developers can understand the API structure by reading the type definitions

3. **Error Prevention**:
   - Catches common issues like missing required fields
   - Validates data types before processing (e.g., numeric vs string fields)
   - Helps prevent data processing errors due to unexpected field formats

4. **API Evolution**:
   - Tracks API changes through type definitions
   - Makes breaking changes obvious through type checking
   - Facilitates versioning and backward compatibility

Implementation Notes:
-------------------
1. **Field Types**:
   - Date fields use string type with format annotations (e.g., 'YYYY-MM-DD')
   - Numeric fields accept both float and int for maximum compatibility
   - Optional fields are marked with `NotRequired` to handle varying responses

2. **Response Structure**:
   - All list endpoints include `metadata` with pagination info
   - Single-item endpoints (e.g., `/datasets/{id}`) return direct objects
   - Rate limit responses have a distinct schema for error handling

3. **Data Handling**:
   - Some numeric fields (e.g., 'datacoverage') may be returned as strings
   - Geographic coordinates are always numeric (float or int)
   - Empty or null values should be handled appropriately in client code

4. **Best Practices**:
   - Always validate response structure against these schemas
   - Handle optional fields defensively
   - Consider caching metadata responses
   - Check for rate limit responses before processing data

Schemas:
--------
 - `ResultSetJSON`: Metadata about pagination (offset, count, limit).
 - `MetadataJSON`: Encapsulates `ResultSetJSON`, included in most responses.
 - `RateLimitJSON`: Response for rate-limiting errors.
 - `DatasetIDJSON`: Response schema for `/datasets/{id}`.
 - `DatasetsJSON`: Response schema for `/datasets`.
 - `DatacategoryIDJSON`: Response schema for `/datacategories/{id}`.
 - `DatacategoriesJSON`: Response schema for `/datacategories`.
 - `DatatypeIDJSON`: Response schema for `/datatypes/{id}`.
 - `DatatypesJSON`: Response schema for `/datatypes`.
 - `LocationcategoryIDJSON`: Response schema for `/locationcategories/{id}`.
 - `LocationcategoriesJSON`: Response schema for `/locationcategories`.
 - `LocationIDJSON`: Response schema for `/locations/{id}`.
 - `LocationsJSON`: Response schema for `/locations`.
 - `StationIDJSON`: Response schema for `/stations/{id}`.
 - `StationsJSON`: Response schema for `/stations`.
 - `DatapointJSON`: Individual data point response from `data?datasetid=...`.
 - `DataJSON`: Response schema for `data?datasetid=...`.

Notes:
------
 - Some fields, such as dates, follow a specific format (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`).
 - Certain fields are `NotRequired`, meaning they may not appear in all responses.
 - Data coverage fields (`datacoverage`) are expressed as a float or integer.
 - Geographic coordinates (latitude, longitude) are always numeric but may be integer or float.
 - Station elevation values include both the numeric value and unit of measurement.
 - Data point values may include quality flags in the optional attributes field.

These schemas facilitate type checking and autocompletion in IDEs while working with the NOAA API responses.
"""  # noqa: E501

from typing import NotRequired, TypedDict


class ResultSetJSON(TypedDict):
    """
    Represents metadata about the result set, including pagination details.
    """  # noqa: E501

    offset: int
    """
    The starting point of the returned results.
    """  # noqa: E501

    count: int
    """
    The total number of results available.
    """  # noqa: E501

    limit: int
    """
    The maximum number of results returned per request.
    """  # noqa: E501


# --- Full JSON Response Structure ---
class MetadataJSON(TypedDict):
    """
    Contains metadata information for a response, including result set details.
    """  # noqa: E501

    resultset: ResultSetJSON
    """
    Pagination and count details of the results.
    """  # noqa: E501


# Rate limit json reponse
class RateLimitJSON(TypedDict):
    """
    Represents the JSON response structure for rate limit information.
    """  # noqa: E501

    status: str
    """
    The status of the rate limit (e.g., 'error').
    """  # noqa: E501

    message: str
    """
    A descriptive message regarding the rate limit status.
    """  # noqa: E501


# Endpoint '/datasets/{id}'


# --- Full JSON Response Structure ---
class DatasetIDJSON(TypedDict):
    """
    Endpoint '/datasets/{id}'
    Represents the JSON response structure for a specific dataset identified by its ID.
    """  # noqa: E501

    mindate: str  # Date as "YYYY-MM-DD"
    """
    The earliest date for which data is available, formatted as 'YYYY-MM-DD'.
    """

    maxdate: str  # Date as "YYYY-MM-DD"
    """
    The latest date for which data is available, formatted as 'YYYY-MM-DD'.
    """

    name: str
    """
    The name of the dataset.
    """

    datacoverage: float | int
    """
    The proportion of data coverage, ranging from 0 to 1.
    """

    id: str
    """
    The unique identifier for the dataset.
    """


# Endpoint '/datasets'


class DatasetJSON(TypedDict):
    """
    Endpoint '/datasets' (subcomponent)
    Represents a dataset within the '/datasets' endpoint response. (subcomponent)
    """  # noqa: E501

    uid: str
    """
    The unique identifier for the dataset.
    """

    mindate: str  # Date as "YYYY-MM-DD"
    """
    The earliest date for which data is available, formatted as 'YYYY-MM-DD'.
    """

    maxdate: str  # Date as "YYYY-MM-DD"
    """
    The latest date for which data is available, formatted as 'YYYY-MM-DD'.
    """

    name: str
    """
    The name of the dataset.
    """

    datacoverage: float | int
    """
    The proportion of data coverage, ranging from 0 to 1.
    """

    id: str
    """
    The unique identifier for the dataset.
    """


# --- Full JSON Response Structure ---
class DatasetsJSON(TypedDict):
    """
    Endpoint '/datasets'
    Represents the JSON response structure for the '/datasets' endpoint.
    """  # noqa: E501

    metadata: MetadataJSON
    """
    Metadata information about the response.
    """

    results: list[DatasetJSON]
    """
    A list of datasets returned in the response.
    """


# Endpoint '/datacategories/{id}'


class DatacategoryIDJSON(TypedDict):
    """
    Endpoint '/datacategories/{id}'
    Represents the JSON response structure for a specific data category identified by its ID.
    """  # noqa: E501

    name: str
    """
    The name of the data category.
    """

    id: str
    """
    The unique identifier for the data category.
    """


# Endpoint '/datacategories'


class DatacategoriesJSON(TypedDict):
    """
    Endpoint '/datacategories'
    Represents the JSON response structure for the '/datacategories' endpoint.
    """  # noqa: E501

    metadata: MetadataJSON
    """
    Metadata information about the response.
    """

    results: list[DatacategoryIDJSON]
    """
    A list of data categories returned in the response.
    """


# Endpoint '/datatypes/{id}'


class DatatypeIDJSON(TypedDict):
    """
    Endpoint '/datatypes/{id}'
    Represents the JSON response structure for a specific data type identified by its ID.
    """  # noqa: E501

    mindate: str  # Date as "YYYY-MM-DD"
    """
    The earliest date for which the data type is available, formatted as 'YYYY-MM-DD'.
    """

    maxdate: str  # Date as "YYYY-MM-DD"
    """
    The latest date for which the data type is available, formatted as 'YYYY-MM-DD'.
    """

    datacoverage: float | int
    """
    The proportion of data coverage for the data type.
    """

    id: str
    """
    The unique identifier for the data type.
    """


# Endpoint '/datatypes'


class DatatypeJSON(TypedDict):
    """
    Endpoint '/datatypes'
    Represents a data type within the '/datatypes' endpoint response. (subcomponent)
    """  # noqa: E501

    mindate: str  # Date as "YYYY-MM-DD"
    """
    The earliest date for which the data type is available, formatted as 'YYYY-MM-DD'.
    """

    maxdate: str  # Date as "YYYY-MM-DD"
    """
    The latest date for which the data type is available, formatted as 'YYYY-MM-DD'.
    """

    name: str
    """
    The name of the data type.
    """

    datacoverage: float | int
    """
    The proportion of data coverage for the data type.
    """

    id: str
    """
    The unique identifier for the data type.
    """


class DatatypesJSON(TypedDict):
    """
    Endpoint '/datatypes'
    Represents the JSON response structure for the '/datatypes' endpoint.
    """  # noqa: E501

    metadata: MetadataJSON
    """
    Metadata information about the response.
    """

    results: list[DatatypeJSON]
    """
    A list of data types returned in the response.
    """


# Endpoint '/locationcategories/{id}'


class LocationcategoryIDJSON(TypedDict):
    """
    Endpoint '/locationcategories/{id}'
    Represents the JSON response structure for a specific location category identified by its ID.
    """  # noqa: E501

    name: str
    """
    The name of the location category.
    """

    id: str
    """
    The unique identifier for the location category.
    """


# Endpoint '/locationcategories'


class LocationcategoriesJSON(TypedDict):
    """
    Endpoint '/locationcategories'
    Represents the JSON response structure for the '/locationcategories' endpoint.
    """  # noqa: E501

    metadata: MetadataJSON
    """
    Metadata information about the response.
    """

    results: list[LocationcategoryIDJSON]
    """
    A list of location categories returned in the response.
    """


# Endpoint '/locations/{id}'


class LocationIDJSON(TypedDict):
    """
    Endpoint '/locations/{id}'
    Represents the JSON response structure for a specific location identified by its ID.
    """  # noqa: E501

    mindate: str  # Date as "YYYY-MM-DD"
    """
    The earliest date for which data is available for the location, formatted as 'YYYY-MM-DD'.
    """  # noqa: E501

    maxdate: str  # Date as "YYYY-MM-DD"
    """
    The latest date for which data is available for the location, formatted as 'YYYY-MM-DD'.
    """  # noqa: E501

    name: str
    """
    The name of the location.
    """

    datacoverage: float | int
    """
    The proportion of data coverage for the location.
    """

    id: str
    """
    The unique identifier for the location.
    """


# Endpoint '/locations'


class LocationsJSON(TypedDict):
    """
    Endpoint '/locations'
    Represents the JSON response structure for the '/locations' endpoint.
    """  # noqa: E501

    metadata: MetadataJSON
    """
    Metadata information about the response, including pagination details.
    """

    results: list[LocationIDJSON]
    """
    A list of location records returned by the query.
    """


# Endpoint '/stations/{id}'


class StationIDJSON(TypedDict):
    """
    Endpoint '/stations/{id}'
    Represents the JSON response structure for a specific station identified by its ID from the '/stations/{id}' endpoint.
    """  # noqa: E501

    elevation: int | float
    """
    The elevation of the station in meters.
    """

    mindate: str  # Date as "YYYY-MM-DD"
    """
    The earliest date for which data is available, formatted as 'YYYY-MM-DD'.
    """

    maxdate: str  # Date as "YYYY-MM-DD"
    """
    The latest date for which data is available, formatted as 'YYYY-MM-DD'.
    """

    latitude: float | int
    """
    The latitude coordinate of the station.
    """

    name: str
    """
    The name of the station.
    """

    datacoverage: float | int
    """
    The proportion of data coverage, ranging from 0 to 1.
    """

    id: str
    """
    The unique identifier for the station.
    """

    elevationUnit: str
    """
    The unit of measurement for elevation (e.g., 'METERS').
    """

    longitude: float | int
    """
    The longitude coordinate of the station.
    """


# Endpoint '/stations'


class StationsJSON(TypedDict):
    """
    Endpoint '/stations'
    Represents the JSON response structure for the '/stations' endpoint.
    """  # noqa: E501

    metadata: MetadataJSON
    """
    Metadata information about the response, including pagination details.
    """

    results: list[StationIDJSON]
    """
    A list of station records returned by the query.
    """


# Endpoint 'data?datasetid=YOUR_DATASETID'


class DatapointJSON(TypedDict):
    """
    Endpoint '/data?datasetid=YOUR_DATASETID' (subcomponent)
    Represents a single data point in the response from the 'data?datasetid=YOUR_DATASETID' endpoint. (subcomponent)
    """  # noqa: E501

    date: str  # Date as "YYYY-MM-DDTHH:MM:SS"
    """
    The date and time of the observation, formatted as 'YYYY-MM-DDTHH:MM:SS'.
    """

    datatype: str
    """
    The type of data recorded (e.g., temperature, precipitation).
    """

    station: str
    """
    The identifier of the station where the data was recorded.
    """

    attributes: NotRequired[str]
    """
    Additional attributes or flags associated with the data point.
    """

    value: float | int
    """
    The recorded value of the data point.
    """


class DataJSON(TypedDict):
    """
    Endpoint '/data?datasetid=YOUR_DATASETID'
    Represents the full JSON response structure for the '/data?datasetid=YOUR_DATASETID' endpoint.
    """  # noqa: E501

    metadata: MetadataJSON
    """
    Metadata information about the response, including pagination details.
    """

    results: list[DatapointJSON]
    """
    A list of data points returned by the query.
    """

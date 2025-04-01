from typing import NotRequired, TypedDict


class ResultSetJSON(TypedDict):
    """
    Represents metadata about the result set, including pagination details.

    Attributes:
        offset (int): The starting point of the returned results.
        count (int): The total number of results available.
        limit (int): The maximum number of results returned per request.
    """  # noqa: E501

    offset: int
    count: int
    limit: int


# --- Full JSON Response Structure ---
class MetadataJSON(TypedDict):
    """
    Contains metadata information for a response, including result set details.

    Attributes:
        resultset (ResultSetJSON): Pagination and count details of the results.
    """  # noqa: E501

    resultset: ResultSetJSON


# Rate limit json reponse
class RateLimitJSON(TypedDict):
    """
    Represents the JSON response structure for rate limit information.

    Attributes:
        status (str): The status of the rate limit (e.g., 'error').
        message (str): A descriptive message regarding the rate limit status.
    """  # noqa: E501

    status: str
    message: str


# Endpoint '/datasets/{id}'


# --- Full JSON Response Structure ---
class DatasetIDJSON(TypedDict):
    """
    Endpoint '/datasets/{id}'
    Represents the JSON response structure for a specific dataset identified by its ID.

    Attributes:
        mindate (str): The earliest date for which data is available, formatted as 'YYYY-MM-DD'.
        maxdate (str): The latest date for which data is available, formatted as 'YYYY-MM-DD'.
        name (str): The name of the dataset. datacoverage (float | int): The proportion of data coverage, ranging from 0 to 1.
        id (str): The unique identifier for the dataset.
    """  # noqa: E501

    mindate: str  # Date as "YYYY-MM-DD"
    maxdate: str  # Date as "YYYY-MM-DD"
    name: str
    datacoverage: float | int
    id: str


# Endpoint '/datasets'


class DatasetJSON(TypedDict):
    """
    Endpoint '/datasets' (subcomponent)
    Represents a dataset within the '/datasets' endpoint response. (subcomponent)

    Attributes:
        uid (str): The unique identifier for the dataset.
        mindate (str): The earliest date for which data is available, formatted as 'YYYY-MM-DD'.
        maxdate (str): The latest date for which data is available, formatted as 'YYYY-MM-DD'.
        name (str): The name of the dataset. datacoverage (float | int): The proportion of data coverage, ranging from 0 to 1.
        id (str): The unique identifier for the dataset.
    """  # noqa: E501

    uid: str
    mindate: str  # Date as "YYYY-MM-DD"
    maxdate: str  # Date as "YYYY-MM-DD"
    name: str
    datacoverage: float | int
    id: str


# --- Full JSON Response Structure ---
class DatasetsJSON(TypedDict):
    """
    Endpoint '/datasets'
    Represents the JSON response structure for the '/datasets' endpoint.

    Attributes:
        metadata (MetadataJSON): Metadata information about the response.
        results (list[DatasetJSON]): A list of datasets returned in the response.
    """  # noqa: E501

    metadata: MetadataJSON
    results: list[DatasetJSON]


# Endpoint '/datacategories/{id}'


class DatacategoryIDJSON(TypedDict):
    """
    Endpoint '/datacategories/{id}'
    Represents the JSON response structure for a specific data category identified by its ID.

    Attributes:
        name (str): The name of the data category.
        id (str): The unique identifier for the data category.
    """  # noqa: E501

    name: str
    id: str


# Endpoint '/datacategories'


class DatacategoriesJSON(TypedDict):
    """
    Endpoint '/datacategories'
    Represents the JSON response structure for the '/datacategories' endpoint.

    Attributes:
        metadata (MetadataJSON): Metadata information about the response.
        results (list[DatacategoryIDJSON]): A list of data categories returned in the response.
    """  # noqa: E501

    metadata: MetadataJSON
    results: list[DatacategoryIDJSON]


# Endpoint '/datatypes/{id}'


class DatatypeIDJSON(TypedDict):
    """
    Endpoint '/datatypes/{id}'
    Represents the JSON response structure for a specific data type identified by its ID.

    Attributes:
        mindate (str): The earliest date for which the data type is available, formatted as 'YYYY-MM-DD'.
        maxdate (str): The latest date for which the data type is available, formatted as 'YYYY-MM-DD'.
        datacoverage (float | int): The proportion of data coverage for the data type.
        id (str): The unique identifier for the data type.
    """  # noqa: E501

    mindate: str  # Date as "YYYY-MM-DD"
    maxdate: str  # Date as "YYYY-MM-DD"
    datacoverage: float | int
    id: str


# Endpoint '/datatypes'


class DatatypeJSON(TypedDict):
    """
    Endpoint '/datatypes'
    Represents a data type within the '/datatypes' endpoint response. (subcomponent)

    Attributes:
        mindate (str): The earliest date for which the data type is available, formatted as 'YYYY-MM-DD'.
        maxdate (str): The latest date for which the data type is available, formatted as 'YYYY-MM-DD'.
        name (str): The name of the data type.
        datacoverage (float | int): The proportion of data coverage for the data type.
        id (str): The unique identifier for the data type.
    """  # noqa: E501

    mindate: str  # Date as "YYYY-MM-DD"
    maxdate: str  # Date as "YYYY-MM-DD"
    name: str
    datacoverage: float | int
    id: str


class DatatypesJSON(TypedDict):
    """
    Endpoint '/datatypes'
    Represents the JSON response structure for the '/datatypes' endpoint.

    Attributes:
        metadata (MetadataJSON): Metadata information about the response.
        results (list[DatatypeJSON]): A list of data types returned in the response.
    """  # noqa: E501

    metadata: MetadataJSON
    results: list[DatatypeJSON]


# Endpoint '/locationcategories/{id}'


class LocationcategoryIDJSON(TypedDict):
    """
    Endpoint '/locationcategories/{id}'
    Represents the JSON response structure for a specific location category identified by its ID.

    Attributes:
        name (str): The name of the location category.
        id (str): The unique identifier for the location category.
    """  # noqa: E501

    name: str
    id: str


# Endpoint '/locationcategories'


class LocationcategoriesJSON(TypedDict):
    """
    Endpoint '/locationcategories'
    Represents the JSON response structure for the '/locationcategories' endpoint.

    Attributes:
        metadata (MetadataJSON): Metadata information about the response.
        results (list[LocationcategoryIDJSON]): A list of location categories returned in the response.
    """  # noqa: E501

    metadata: MetadataJSON
    results: list[LocationcategoryIDJSON]


# Endpoint '/locations/{id}'


class LocationIDJSON(TypedDict):
    """
    Endpoint '/locations/{id}'
    Represents the JSON response structure for a specific location identified by its ID.

    Attributes:
        mindate (str): The earliest date for which data is available for the location, formatted as 'YYYY-MM-DD'.
        maxdate (str): The latest date for which data is available for the location, formatted as 'YYYY-MM-DD'.
        name (str): The name of the location.
        datacoverage (float | int): The proportion of data coverage for the location.
        id (str): The unique identifier for the location.
    """  # noqa: E501

    mindate: str  # Date as "YYYY-MM-DD"
    maxdate: str  # Date as "YYYY-MM-DD"
    name: str
    datacoverage: float | int
    id: str


# Endpoint '/locations'


class LocationsJSON(TypedDict):
    """
    Endpoint '/locations'
    Represents the JSON response structure for the '/locations' endpoint.

    Attributes:
        metadata (MetadataJSON): Metadata information about the response, including pagination details.
        results (list[LocationIDJSON]): A list of location records returned by the query.
    """  # noqa: E501

    metadata: MetadataJSON
    results: list[LocationIDJSON]


# Endpoint '/stations/{id}'


class StationIDJSON(TypedDict):
    """
    Endpoint '/stations/{id}'
    Represents the JSON response structure for a specific station identified by its ID from the '/stations/{id}' endpoint.

    Attributes:
        elevation (float): The elevation of the station in meters.
        mindate (str): The earliest date for which data is available, formatted as 'YYYY-MM-DD'.
        maxdate (str): The latest date for which data is available, formatted as 'YYYY-MM-DD'.
        latitude (float): The latitude coordinate of the station.
        name (str): The name of the station.
        datacoverage (float | int): The proportion of data coverage, ranging from 0 to 1.
        id (str): The unique identifier for the station.
        elevationUnit (str): The unit of measurement for elevation (e.g., 'METERS').
        longitude (float): The longitude coordinate of the station.
    """  # noqa: E501

    elevation: float
    mindate: str  # Date as "YYYY-MM-DD"
    maxdate: str  # Date as "YYYY-MM-DD"
    latitude: float
    name: str
    datacoverage: float | int
    id: str
    elevationUnit: str
    longitude: float


# Endpoint '/stations'


class StationsJSON(TypedDict):
    """
    Endpoint '/stations'
    Represents the JSON response structure for the '/stations' endpoint.

    Attributes:
        metadata (MetadataJSON): Metadata information about the response, including pagination details.
        results (list[StationIDJSON]): A list of station records returned by the query.
    """  # noqa: E501

    metadata: MetadataJSON
    results: list[StationIDJSON]


# Endpoint 'data?datasetid=YOUR_DATASETID'


class DatapointJSON(TypedDict):
    """
    Endpoint '/data?datasetid=YOUR_DATASETID' (subcomponent)
    Represents a single data point in the response from the 'data?datasetid=YOUR_DATASETID' endpoint. (subcomponent)

    Attributes:
        date (str): The date and time of the observation, formatted as 'YYYY-MM-DDTHH:MM:SS'.
        datatype (str): The type of data recorded (e.g., temperature, precipitation).
        station (str): The identifier of the station where the data was recorded.
        attributes (NotRequired[str]): Additional attributes or flags associated with the data point.
        value (float | int): The recorded value of the data point.
    """  # noqa: E501

    date: str  # Date as "YYYY-MM-DDTHH:MM:SS"
    datatype: str
    station: str
    attributes: NotRequired[str]
    value: float | int


class DataJSON(TypedDict):
    """
    Endpoint '/data?datasetid=YOUR_DATASETID'
    Represents the full JSON response structure for the '/data?datasetid=YOUR_DATASETID' endpoint.

    Attributes:
        metadata (MetadataJSON): Metadata information about the response, including pagination details.
        results (list[DatapointJSON]): A list of data points returned by the query.
    """  # noqa: E501

    metadata: MetadataJSON
    results: list[DatapointJSON]

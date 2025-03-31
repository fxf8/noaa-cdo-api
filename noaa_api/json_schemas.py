from typing import TypedDict, Literal


class ResultSetJSON(TypedDict):
    offset: int
    count: int
    limit: int


# --- Full JSON Response Structure ---
class MetadataJSON(TypedDict):
    resultset: ResultSetJSON


# Endpoint '/datasets/{id}'


# --- Full JSON Response Structure ---
class DatasetIDJSON(TypedDict):
    """
    Full JSON Response for endpoint '/datasets/{id}'
    """

    mindate: str  # Date as "YYYY-MM-DD"
    maxdate: str  # Date as "YYYY-MM-DD"
    name: str
    datacoverage: float | int
    id: str


# Endpoint '/datasets'


class DatasetJSON(TypedDict):
    """
    JSON Subcomponent for endpoint '/datasets'
    """

    uid: str
    mindate: str  # Date as "YYYY-MM-DD"
    maxdate: str  # Date as "YYYY-MM-DD"
    name: str
    datacoverage: float | int
    id: str


# --- Full JSON Response Structure ---
class DatasetsJSON(TypedDict):
    """
    Full JSON Response for endpoint '/datasets'
    """

    metadata: MetadataJSON
    results: list[DatasetJSON]


# Endpoint '/datacategories/{id}'


class DatacategoryIDJSON(TypedDict):
    """
    Full JSON Response for endpoint '/datacategories/{id}'
    """

    name: str
    id: str


# Endpoint '/datacategories'


class DatacategoriesJSON(TypedDict):
    """
    Full JSON Response for endpoint '/datacategories'
    """

    metadata: MetadataJSON
    results: list[DatacategoryIDJSON]


# Endpoint '/datatypes/{id}'


class DatatypeIDJSON(TypedDict):
    """
    Full JSON Response for endpoint '/datatypes/{id}'
    """

    mindate: str  # Date as "YYYY-MM-DD"
    maxdate: str  # Date as "YYYY-MM-DD"
    datacoverage: float | int
    id: str


# Endpoint '/datatypes'


class DatatypeJSON(TypedDict):
    """
    JSON Subcomponent for endpoint '/datatypes'
    """

    mindate: str  # Date as "YYYY-MM-DD"
    maxdate: str  # Date as "YYYY-MM-DD"
    name: str
    datacoverage: float | int
    id: str


class DatatypesJSON(TypedDict):
    """
    Full JSON Response for endpoint '/datatypes'
    """

    metadata: MetadataJSON
    results: list[DatatypeJSON]


# Endpoint '/locationcategories/{id}'


class LocationcategoryIDJSON(TypedDict):
    """
    Full JSON Response for endpoint '/locationcategories/{id}'
    """

    name: str
    id: str


# Endpoint '/locationcategories'


class LocationcategoriesJSON(TypedDict):
    """
    Full JSON Response for endpoint '/locationcategories'
    """

    metadata: MetadataJSON
    results: list[LocationcategoryIDJSON]


# Endpoint '/locations/{id}'


class LocationIDJSON(TypedDict):
    """
    Full JSON Response for endpoint '/locations/{id}'
    """

    mindate: str  # Date as "YYYY-MM-DD"
    maxdate: str  # Date as "YYYY-MM-DD"
    name: str
    datacoverage: float | int
    id: str


# Endpoint '/locations'


class LocationsJSON(TypedDict):
    """
    Full JSON Response for endpoint '/locations'
    """

    metadata: MetadataJSON
    results: list[LocationIDJSON]


# Endpoint '/stations/{id}'


class StationIDJSON(TypedDict):
    """
    Full JSON Response for endpoint '/stations/{id}'
    """

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
    Full JSON Response for endpoint '/stations'
    """

    metadata: MetadataJSON
    results: list[StationIDJSON]


# Endpoint 'data?datasetid=YOUR_DATASETID'


class DatapointJSON(TypedDict):
    """
    JSON Subcomponent for endpoint 'data?datasetid=YOUR_DATASETID'
    """

    date: str  # Date as "YYYY-MM-DDTHH:MM:SS"
    datatype: str
    station: str
    attributes: str
    value: float | int


class DataJSON(TypedDict):
    """
    Full JSON Response for endpoint 'data?datasetid=YOUR_DATASETID'
    """

    metadata: MetadataJSON
    results: list[DatapointJSON]


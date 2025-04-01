from typing import TypedDict, Required, Literal


Sortfield = Literal["id", "name", "mindate", "maxdate", "datacoverage", ""]
Sortorder = Literal["asc", "desc"]
Units = Literal["standard", "metric", ""]


class DatasetsParameters(TypedDict, total=False):
    datatypeid: str  # Singular or chain seperated by &
    locationid: str  # Singular or chain seperated by &
    stationid: str  # Singular or chain seperated by &
    startdate: str  # YYYY-MM-DD
    enddate: str  # YYYY-MM-DD
    sortfield: Sortfield  # Default is "id"
    sortorder: Sortorder  # Default is "asc"
    limit: int  # Default is 25. Maximum is 1000
    offset: int  # Default is 0


class DatacategoriesParameters(TypedDict, total=False):
    datasetid: str  # Singular or chain seperated by &
    locationid: str  # Singular or chain seperated by &
    stationid: str  # Singular or chain seperated by &
    startdate: str  # YYYY-MM-DD
    enddate: str  # YYYY-MM-DD
    sortfield: Sortfield  # Default is "id"
    sortorder: Sortorder  # Default is "asc"
    limit: int  # Default is 25. Maximum is 1000
    offset: int  # Default is 0


class DatatypesParameters(TypedDict, total=False):
    datasetid: str  # Singular or chain separated by &
    locationid: str  # Singular or chain separated by &
    stationid: str  # Singular or chain separated by &
    datacategoryid: str  # Singular or chain separated by &
    startdate: str  # YYYY-MM-DD
    enddate: str  # YYYY-MM-DD
    sortfield: Sortfield  # Default is "id"
    sortorder: Sortorder  # Default is "asc"
    limit: int  # Default is 25. Maximum is 1000
    offset: int  # Default is 0


class LocationcategoriesParameters(TypedDict, total=False):
    datasetid: str  # Singular or chain separated by &
    startdate: str  # YYYY-MM-DD
    enddate: str  # YYYY-MM-DD
    sortfield: Sortfield  # Default is "id"
    sortorder: Sortorder  # Default is "asc"
    limit: int  # Default is 25. Maximum is 1000
    offset: int  # Default is 0


class LocationsParameters(TypedDict, total=False):
    datasetid: str  # Singular or chain separated by &
    locationcategoryid: str  # Singular or chain separated by &
    datacategoryid: str  # Singular or array of data category IDs
    startdate: str  # YYYY-MM-DD
    enddate: str  # YYYY-MM-DD
    sortfield: Sortfield  # Default is "id"
    sortorder: Sortorder  # Default is "asc"
    limit: int  # Default is 25. Maximum is 1000
    offset: int  # Default is 0


class StationsParameters(TypedDict, total=False):
    datasetid: str  # Singular or chain separated by &
    locationid: str  # Singular or chain separated by &
    datacategoryid: str  # Singular or array of data category IDs
    datatypeid: str  # Singular or chain separated by &
    extent: str  # Geographical extent (LatLngBounds.toUrlValue format) (latitude_min,longitude_min,latitude_max,longitude_max)
    startdate: str  # YYYY-MM-DD
    enddate: str  # YYYY-MM-DD
    sortfield: Sortfield  # Default is "id"
    sortorder: Sortorder  # Default is "asc"
    limit: int  # Default is 25. Maximum is 1000
    offset: int  # Default is 0


class DataParameters(TypedDict, total=False):
    datasetid: Required[str]  # Required. A valid dataset id
    datatypeid: str  # Singular or chain separated by &
    locationid: str  # Singular or chain separated by &
    stationid: str  # Singular or chain separated by &
    startdate: Required[
        str
    ]  # Required. Valid ISO formatted date (YYYY-MM-DD) or datetime (YYYY-MM-DDThh:mm:ss)
    enddate: Required[
        str
    ]  # Required. Valid ISO formatted date (YYYY-MM-DD) or datetime (YYYY-MM-DDThh:mm:ss)
    # Note: Annual and Monthly data will be limited to a 10 year range while other data will be limited to a 1 year range

    units: Units  # Default is no conversion
    sortfield: Sortfield
    sortorder: Sortorder  # Default is "asc"
    limit: int  # Default is 25. Maximum is 1000
    offset: int  # Default is 0
    includemetadata: (
        bool  # Default is True, set to False to exclude metadata calculation
    )


AnyParameter = (
    DatasetsParameters
    | DatacategoriesParameters
    | DatatypesParameters
    | LocationcategoriesParameters
    | LocationsParameters
    | StationsParameters
    | DataParameters
)

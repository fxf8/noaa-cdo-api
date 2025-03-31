from typing import TypedDict, NotRequired, Literal


class DatasetsParameters(TypedDict):
    datatypeid: NotRequired[str]  # Singular or chain seperated by &
    locationid: NotRequired[str]  # Singular or chain seperated by &
    stationid: NotRequired[str]  # Singular or chain seperated by &
    startdate: NotRequired[str]  # YYYY-MM-DD
    enddate: NotRequired[str]  # YYYY-MM-DD
    sortfield: NotRequired[Literal["id", "name", "mindate", "maxdate", "datacoverage"]]
    sortorder: NotRequired[Literal["asc", "desc"]]  # Default is "asc"
    limit: NotRequired[int]  # Default is 25. Maximum is 1000
    offset: NotRequired[int]  # Default is 0


class DatacategoriesParameters(TypedDict):
    datasetid: NotRequired[str]  # Singular or chain seperated by &
    locationid: NotRequired[str]  # Singular or chain seperated by &
    stationid: NotRequired[str]  # Singular or chain seperated by &
    startdate: NotRequired[str]  # YYYY-MM-DD
    enddate: NotRequired[str]  # YYYY-MM-DD
    sortfield: NotRequired[Literal["id", "name", "mindate", "maxdate", "datacoverage"]]
    sortorder: NotRequired[Literal["asc", "desc"]]  # Default is "asc"
    limit: NotRequired[int]  # Default is 25. Maximum is 1000
    offset: NotRequired[int]  # Default is 0


class DatatypesParameters(TypedDict):
    datasetid: NotRequired[str]  # Singular or chain separated by &
    locationid: NotRequired[str]  # Singular or chain separated by &
    stationid: NotRequired[str]  # Singular or chain separated by &
    datacategoryid: NotRequired[str]  # Singular or chain separated by &
    startdate: NotRequired[str]  # YYYY-MM-DD
    enddate: NotRequired[str]  # YYYY-MM-DD
    sortfield: NotRequired[Literal["id", "name", "mindate", "maxdate", "datacoverage"]]
    sortorder: NotRequired[Literal["asc", "desc"]]  # Default is "asc"
    limit: NotRequired[int]  # Default is 25. Maximum is 1000
    offset: NotRequired[int]  # Default is 0


class LocationcategoriesParameters(TypedDict):
    datasetid: NotRequired[str]  # Singular or chain separated by &
    startdate: NotRequired[str]  # YYYY-MM-DD
    enddate: NotRequired[str]  # YYYY-MM-DD
    sortfield: NotRequired[Literal["id", "name", "mindate", "maxdate", "datacoverage"]]
    sortorder: NotRequired[Literal["asc", "desc"]]  # Default is "asc"
    limit: NotRequired[int]  # Default is 25. Maximum is 1000
    offset: NotRequired[int]  # Default is 0


class LocationsParameters(TypedDict):
    datasetid: NotRequired[str]  # Singular or chain separated by &
    locationcategoryid: NotRequired[str]  # Singular or chain separated by &
    datacategoryid: NotRequired[str]  # Singular or array of data category IDs
    startdate: NotRequired[str]  # YYYY-MM-DD
    enddate: NotRequired[str]  # YYYY-MM-DD
    sortfield: NotRequired[Literal["id", "name", "mindate", "maxdate", "datacoverage"]]
    sortorder: NotRequired[Literal["asc", "desc"]]  # Default is "asc"
    limit: NotRequired[int]  # Default is 25. Maximum is 1000
    offset: NotRequired[int]  # Default is 0


class StationsParameters(TypedDict):
    datasetid: NotRequired[str]  # Singular or chain separated by &
    locationid: NotRequired[str]  # Singular or chain separated by &
    datacategoryid: NotRequired[str]  # Singular or array of data category IDs
    datatypeid: NotRequired[str]  # Singular or chain separated by &
    extent: NotRequired[
        str
    ]  # Geographical extent (LatLngBounds.toUrlValue format) (latitude_min,longitude_min,latitude_max,longitude_max)
    startdate: NotRequired[str]  # YYYY-MM-DD
    enddate: NotRequired[str]  # YYYY-MM-DD
    sortfield: NotRequired[Literal["id", "name", "mindate", "maxdate", "datacoverage"]]
    sortorder: NotRequired[Literal["asc", "desc"]]  # Default is "asc"
    limit: NotRequired[int]  # Default is 25. Maximum is 1000
    offset: NotRequired[int]  # Default is 0


class DataParameters(TypedDict):
    datasetid: str  # Required. A valid dataset id
    datatypeid: NotRequired[str]  # Singular or chain separated by &
    locationid: NotRequired[str]  # Singular or chain separated by &
    stationid: NotRequired[str]  # Singular or chain separated by &
    startdate: str  # Required. Valid ISO formatted date (YYYY-MM-DD) or datetime (YYYY-MM-DDThh:mm:ss)
    enddate: str  # Required. Valid ISO formatted date (YYYY-MM-DD) or datetime (YYYY-MM-DDThh:mm:ss)
    # Note: Annual and Monthly data will be limited to a 10 year range while other data will be limited to a 1 year range

    units: NotRequired[Literal["standard", "metric"]]  # Default is no conversion
    sortfield: NotRequired[Literal["id", "name", "mindate", "maxdate", "datacoverage"]]
    sortorder: NotRequired[Literal["asc", "desc"]]  # Default is "asc"
    limit: NotRequired[int]  # Default is 25. Maximum is 1000
    offset: NotRequired[int]  # Default is 0
    includemetadata: NotRequired[
        bool
    ]  # Default is True, set to False to exclude metadata calculation

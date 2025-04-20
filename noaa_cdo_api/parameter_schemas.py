"""
NOAA API Query Parameter Schemas
================================

This module defines `TypedDict` structures representing valid query parameters for various NOAA NCEI API v2 endpoints. These schemas provide type safety and enforce expected query structures.

Each class corresponds to a specific API endpoint, detailing the expected parameters and their types.

Integration with aiohttp:
----------------------
These parameter schemas are specifically designed to be used with aiohttp's ClientSession.get method's
`params` keyword argument. For example:

```python
async with aiohttp.ClientSession() as session:
    params: parameter_schemas.DatasetsParameters = {
        "datatypeid": "TMAX",
        "startdate": "2020-01-01",
        "limit": 100
    }
    async with session.get("https://api.example.com/datasets", params=params) as response:
        data = await response.json()
```

The schemas ensure that the parameters match aiohttp's expectations for query string generation
(see: https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession.get).
Key features:
- Type safety for parameter values
- Automatic conversion of parameters to proper URL encoding
- Support for multi-value parameters using comma separation
- Validation of enum values (e.g., sortorder, units)

Schemas:
--------
 - `DatasetsParameters`: Parameters for querying `/datasets`.
 - `DatacategoriesParameters`: Parameters for querying `/datacategories`.
 - `DatatypesParameters`: Parameters for querying `/datatypes`.
 - `LocationcategoriesParameters`: Parameters for querying `/locationcategories`.
 - `LocationsParameters`: Parameters for querying `/locations`.
 - `StationsParameters`: Parameters for querying `/stations`.
 - `DataParameters`: Parameters for querying `/data`.

Notes:
------
 - Many parameters support filtering via singular values or chains separated by `,` (e.g., `"GHCND:USW00094728,GHCND:USC00042319"`).
 - Dates must be formatted as `"YYYY-MM-DD"` or `"YYYY-MM-DDThh:mm:ss"`.
 - `sortfield` and `sortorder` control result sorting.
 - `limit` and `offset` allow pagination (default `limit=25`, max `limit=1000`).
 - `units` determines unit conversion (`"standard"` or `"metric"`).
 - `includemetadata` is a boolean flag to include or exclude metadata from responses.
 - `extent` (in `StationsParameters`) defines a bounding box for geographic filtering. (format: "latitude_min,longitude_min,latitude_max,longitude_max")

Advanced Usage:
-------------
1. Multi-value Parameters:
   ```python
   params: parameter_schemas.StationsParameters = {
       "stationid": "GHCND:USW00094728,GHCND:USC00042319",
       # OR as a joined list
       "stationid": ",".join(["GHCND:USW00094728", "GHCND:USC00042319"])
   }
   ```

2. Geographic Filtering:
   ```python
   params: parameter_schemas.StationsParameters = {
       "extent": "40.0,-90.0,42.0,-88.0",  # latitude_min,longitude_min,latitude_max,longitude_max
       "datasetid": "GHCND"
   }
   ```

3. Required Parameters:
   ```python
   params: parameter_schemas.DataParameters = {
       "datasetid": "GHCND",  # Required
       "startdate": "2020-01-01",  # Required
       "enddate": "2020-12-31",  # Required
       "units": "metric"  # Optional
   }
   ```

These schemas facilitate type checking and autocompletion in IDEs while working with the NOAA API.
"""  # noqa: E501

from typing import Literal, Required, TypedDict

Sortfield = Literal["id", "name", "mindate", "maxdate", "datacoverage", ""]
"""
Literal set of values for the api 'sortfield'. Only for DatasetsParameters, DatacategoriesParameters, DatatypesParameters, LocationcategoriesParameters, LocationsParameters, StationsParameters. **NOT for DataParameters**
"""  # noqa: E501
DataSortField = Literal["datatype", "date", "station"]

Sortorder = Literal["asc", "desc"]
"""
Literal set of values for the api 'sortorder' (ascend or descend)
"""

Units = Literal["standard", "metric", ""]
"""
Literal set of values for 'units' parameter in DataParameters. Default value yields no conversion.
"""  # noqa: E501


class DatasetsParameters(TypedDict, total=False):
    """
    Parameters for querying the `/datasets` endpoint of the NOAA NCEI API v2.
    """  # noqa: E501

    datatypeid: str  # Singular or chain seperated by ','
    """
    Filter by data type ID(s). Can be a single value or multiple values separated by ','.
    """  # noqa: E501

    locationid: str  # Singular or chain seperated by ','
    """
    Filter by location ID(s). Can be a single value or multiple values separated by ','.
    """  # noqa: E501

    stationid: str  # Singular or chain seperated by ','
    """
    Filter by station ID(s). Can be a single value or multiple values separated by ','.
    """

    startdate: str  # YYYY-MM-DD
    """
    Beginning of date range in 'YYYY-MM-DD' format.
    """

    enddate: str  # YYYY-MM-DD
    """
    End of date range in 'YYYY-MM-DD' format.
    """

    sortfield: Sortfield  # Default is "id"
    """
    Field to sort results by. Options are "id", "name", "mindate", "maxdate", "datacoverage". Default is "id".
    """  # noqa: E501

    sortorder: Sortorder  # Default is "asc"
    """
    Sort direction, either "asc" (ascending) or "desc" (descending). Default is "asc".
    """

    limit: int  # Default is 25. Maximum is 1000
    """
    Maximum number of results to return. Default is 25, maximum is 1000.
    """

    offset: int  # Default is 0
    """
    Number of results to skip for pagination. Default is 0.
    """


class DatacategoriesParameters(TypedDict, total=False):
    """
    Parameters for querying the `/datacategories` endpoint of the NOAA NCEI API v2.
    """  # noqa: E501

    datasetid: str  # Singular or chain seperated by ','
    """
    Filter by dataset ID(s). Can be a single value or multiple values separated by ','.
    """

    locationid: str  # Singular or chain seperated by ','
    """
    Filter by location ID(s). Can be a single value or multiple values separated by ','.
    """

    stationid: str  # Singular or chain seperated by ','
    """
    Filter by station ID(s). Can be a single value or multiple values separated by ','.
    """

    startdate: str  # YYYY-MM-DD
    """
    Beginning of date range in 'YYYY-MM-DD' format.
    """

    enddate: str  # YYYY-MM-DD
    """
    End of date range in 'YYYY-MM-DD' format.
    """

    sortfield: Sortfield  # Default is "id"
    """
    Field to sort results by. Options are "id", "name", "mindate", "maxdate", "datacoverage". Default is "id".
    """  # noqa: E501

    sortorder: Sortorder  # Default is "asc"
    """
    Sort direction, either "asc" (ascending) or "desc" (descending). Default is "asc".
    """

    limit: int  # Default is 25. Maximum is 1000
    """
    Maximum number of results to return. Default is 25, maximum is 1000.
    """

    offset: int  # Default is 0
    """
    Number of results to skip for pagination. Default is 0.
    """


class DatatypesParameters(TypedDict, total=False):
    """
    Parameters for querying the `/datatypes` endpoint of the NOAA NCEI API v2.
    """  # noqa: E501

    datasetid: str  # Singular or chain separated by ','
    """
    Filter by dataset ID(s). Can be a single value or multiple values separated by ','.
    """

    locationid: str  # Singular or chain separated by ','
    """
    Filter by location ID(s). Can be a single value or multiple values separated by ','.
    """

    stationid: str  # Singular or chain separated by ','
    """
    Filter by station ID(s). Can be a single value or multiple values separated by ','.
    """

    datacategoryid: str  # Singular or chain separated by ','
    """
    Filter by data category ID(s). Can be a single value or multiple values separated by ','.
    """  # noqa: E501

    startdate: str  # YYYY-MM-DD
    """
    Beginning of date range in 'YYYY-MM-DD' format.
    """

    enddate: str  # YYYY-MM-DD
    """
    End of date range in 'YYYY-MM-DD' format.
    """

    sortfield: Sortfield  # Default is "id"
    """
    Field to sort results by. Options are "id", "name", "mindate", "maxdate", "datacoverage". Default is "id".
    """  # noqa: E501

    sortorder: Sortorder  # Default is "asc"
    """
    Sort direction, either "asc" (ascending) or "desc" (descending). Default is "asc".
    """

    limit: int  # Default is 25. Maximum is 1000
    """
    Maximum number of results to return. Default is 25, maximum is 1000.
    """

    offset: int  # Default is 0
    """
    Number of results to skip for pagination. Default is 0.
    """


class LocationcategoriesParameters(TypedDict, total=False):
    """
    Parameters for querying the `/locationcategories` endpoint of the NOAA NCEI API v2.
    """  # noqa: E501

    datasetid: str  # Singular or chain separated by ','
    """
    Filter by dataset ID(s). Can be a single value or multiple values separated by ','.
    """

    startdate: str  # YYYY-MM-DD
    """
    Beginning of date range in 'YYYY-MM-DD' format.
    """

    enddate: str  # YYYY-MM-DD
    """
    End of date range in 'YYYY-MM-DD' format.
    """

    sortfield: Sortfield  # Default is "id"
    """
    Field to sort results by. Options are "id", "name", "mindate", "maxdate", "datacoverage". Default is "id".
    """  # noqa: E501

    sortorder: Sortorder  # Default is "asc"
    """
    Sort direction, either "asc" (ascending) or "desc" (descending). Default is "asc".
    """

    limit: int  # Default is 25. Maximum is 1000
    """
    Maximum number of results to return. Default is 25, maximum is 1000.
    """

    offset: int  # Default is 0
    """
    Number of results to skip for pagination. Default is 0.
    """


class LocationsParameters(TypedDict, total=False):
    """
    Parameters for querying the `/locations` endpoint of the NOAA NCEI API v2.
    """  # noqa: E501

    datasetid: str  # Singular or chain separated by ','
    """
    Filter by dataset ID(s). Can be a single value or multiple values separated by ','.
    """

    locationcategoryid: str  # Singular or chain separated by ','
    """
    Filter by location category ID(s). Can be a single value or multiple values separated by ','.
    """  # noqa: E501

    datacategoryid: str  # Singular or array of data category IDs
    """
    Filter by data category ID(s). Can be a single value or an array of data category IDs.
    """  # noqa: E501

    startdate: str  # YYYY-MM-DD
    """
    Beginning of date range in 'YYYY-MM-DD' format.
    """

    enddate: str  # YYYY-MM-DD
    """
    End of date range in 'YYYY-MM-DD' format.
    """

    sortfield: Sortfield  # Default is "id"
    """
    Field to sort results by. Options are "id", "name", "mindate", "maxdate", "datacoverage". Default is "id".
    """  # noqa: E501

    sortorder: Sortorder  # Default is "asc"
    """
    Sort direction, either "asc" (ascending) or "desc" (descending). Default is "asc".
    """

    limit: int  # Default is 25. Maximum is 1000
    """
    Maximum number of results to return. Default is 25, maximum is 1000.
    """

    offset: int  # Default is 0
    """
    Number of results to skip for pagination. Default is 0.
    """


class StationsParameters(TypedDict, total=False):
    """
    Parameters for querying the `/stations` endpoint of the NOAA NCEI API v2.
    """  # noqa: E501

    datasetid: str  # Singular or chain separated by ','
    """
    Filter by dataset ID(s). Can be a single value or multiple values separated by ','.
    """

    locationid: str  # Singular or chain separated by ','
    """
    Filter by location ID(s). Can be a single value or multiple values separated by ','.
    """

    datacategoryid: str  # Singular or array of data category IDs
    """
    Filter by data category ID(s). Can be a single value or an array of data category IDs.
    """  # noqa: E501

    datatypeid: str  # Singular or chain separated by ','
    """
    Filter by data type ID(s). Can be a single value or multiple values separated by ','.
    """  # noqa: E501

    extent: str  # Geographical extent (latitude_min,longitude_min,latitude_max,longitude_max)  # noqa: E501
    """
    Geographical bounding box in format "latitude_min,longitude_min,latitude_max,longitude_max". (LatLngBounds.toUrlValue format)
    """  # noqa: E501

    startdate: str  # YYYY-MM-DD
    """
    Beginning of date range in 'YYYY-MM-DD' format.
    """

    enddate: str  # YYYY-MM-DD
    """
    End of date range in 'YYYY-MM-DD' format.
    """

    sortfield: Sortfield  # Default is "id"
    """
    Field to sort results by. Options are "id", "name", "mindate", "maxdate", "datacoverage". Default is "id".
    """  # noqa: E501

    sortorder: Sortorder  # Default is "asc"
    """
    Sort direction, either "asc" (ascending) or "desc" (descending). Default is "asc".
    """

    limit: int  # Default is 25. Maximum is 1000
    """
    Maximum number of results to return. Default is 25, maximum is 1000.
    """

    offset: int  # Default is 0
    """
    Number of results to skip for pagination. Default is 0.
    """


class DataParameters(TypedDict, total=False):
    """
    Parameters for querying the `/data` endpoint of the NOAA NCEI API v2.
    """  # noqa: E501

    datasetid: Required[str]  # Required. A valid dataset id
    """
    Required. A valid dataset ID.
    """

    datatypeid: str  # Singular or chain separated by ','
    """
    Filter by data type ID(s). Can be a single value or multiple values separated by ','.
    """  # noqa: E501

    locationid: str  # Singular or chain separated by ','
    """
    Filter by location ID(s). Can be a single value or multiple values separated by ','.
    """

    stationid: str  # Singular or chain separated by ','
    """
    Filter by station ID(s). Can be a single value or multiple values separated by ','.
    """

    startdate: Required[
        str
    ]  # Required. Valid ISO formatted date (YYYY-MM-DD) or datetime (YYYY-MM-DDThh:mm:ss)  # noqa: E501
    """
    Required. Beginning of date range in 'YYYY-MM-DD' format or 'YYYY-MM-DDThh:mm:ss' datetime format.
    """  # noqa: E501

    enddate: Required[
        str
    ]  # Required. Valid ISO formatted date (YYYY-MM-DD) or datetime (YYYY-MM-DDThh:mm:ss)  # noqa: E501
    # Note: Annual and Monthly data will be limited to a 10 year range while other data will be limited to a 1 year range  # noqa: E501
    """
    Required. End of date range in 'YYYY-MM-DD' format or 'YYYY-MM-DDThh:mm:ss' datetime format.
    Note: Annual and monthly data will be limited to a 10-year range while other data will be limited to a 1-year range.
    """  # noqa: E501

    units: Units  # Default is no conversion
    """
    Unit conversion, either "standard" or "metric". Default is no conversion.
    """

    sortfield: DataSortField
    """
    Field to sort results by. Options are "id", "name", "mindate", "maxdate", "datacoverage".
    """  # noqa: E501

    sortorder: Sortorder  # Default is "asc"
    """
    Sort direction, either "asc" (ascending) or "desc" (descending). Default is "asc".
    """

    limit: int  # Default is 25. Maximum is 1000
    """
    Maximum number of results to return. Default is 25, maximum is 1000.
    """

    offset: int  # Default is 0
    """
    Number of results to skip for pagination. Default is 0.
    """

    includemetadata: (
        str  # Default is True, set to False to exclude metadata calculation
    )
    """
    Whether to include metadata in the response. Default is True.
    """


AnyParameter = (
    DatasetsParameters
    | DatacategoriesParameters
    | DatatypesParameters
    | LocationcategoriesParameters
    | LocationsParameters
    | StationsParameters
    | DataParameters
)
"""
Union type representing any valid NOAA API parameter dictionary.
Can be one of:
- DatasetsParameters
- DatacategoriesParameters
- DatatypesParameters
- LocationcategoriesParameters
- LocationsParameters
- StationsParameters
- DataParameters
"""

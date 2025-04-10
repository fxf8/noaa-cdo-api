"""
This module defines JSON response schemas for various NOAA API endpoints (as opposed to all schemas in `noaa_cdo_api.json_schemas`).

Each schema represents a structured format returned by the NOAA API, allowing for type validation and easier integration when handling API responses. These schemas are derived from `noaa_cdo_api.json_schemas` and provide standardized representations of datasets, locations, stations, and other NOAA data.

Available Schemas:
 - RateLimitJSON: Response format for API rate limits.
 - DatasetIDJSON, DatasetsJSON: Schema for NOAA datasets.
 - DatacategoryIDJSON, DatacategoriesJSON: Schema for data categories.
 - DatatypeIDJSON, DatatypesJSON: Schema for data types.
 - LocationcategoryIDJSON, LocationcategoriesJSON: Schema for location categories.
 - LocationIDJSON, LocationsJSON: Schema for locations.
 - StationIDJSON, StationsJSON: Schema for weather stations.

These schemas ensure structured API responses for reliable data handling.
"""  # noqa: E501

import noaa_cdo_api.json_schemas as json_schemas

RateLimitJSON = json_schemas.RateLimitJSON
DatasetIDJSON = json_schemas.DatasetIDJSON
DatasetsJSON = json_schemas.DatasetsJSON
DatacategoryIDJSON = json_schemas.DatacategoryIDJSON
DatacategoriesJSON = json_schemas.DatacategoriesJSON
DatatypeIDJSON = json_schemas.DatatypeIDJSON
DatatypesJSON = json_schemas.DatatypesJSON
LocationcategoryIDJSON = json_schemas.LocationcategoryIDJSON
LocationcategoriesJSON = json_schemas.LocationcategoriesJSON
LocationIDJSON = json_schemas.LocationIDJSON
LocationsJSON = json_schemas.LocationsJSON
StationIDJSON = json_schemas.StationIDJSON
StationsJSON = json_schemas.StationsJSON
DataJSON = json_schemas.DataJSON

AnyResponse = (
    RateLimitJSON
    | DatasetIDJSON
    | DatasetsJSON
    | DatacategoryIDJSON
    | DatacategoriesJSON
    | DatatypeIDJSON
    | DatatypesJSON
    | LocationcategoryIDJSON
    | LocationcategoriesJSON
    | LocationIDJSON
    | LocationsJSON
    | StationIDJSON
    | StationsJSON
)
"""
Union type representing any possible response schema from the NOAA API from documented endpoints.
"""  # noqa: E501

__all__ = [
    "RateLimitJSON",
    "DatasetIDJSON",
    "DatasetsJSON",
    "DatacategoryIDJSON",
    "DatacategoriesJSON",
    "DatatypeIDJSON",
    "DatatypesJSON",
    "LocationcategoryIDJSON",
    "LocationcategoriesJSON",
    "LocationIDJSON",
    "LocationsJSON",
    "StationIDJSON",
    "StationsJSON",
    "AnyResponse",
]

import json
import os

from dash import Dash, html, dcc, callback, Output, Input, no_update, dash_table
from fastkml import kml
import numpy as np
import plotly.graph_objects as go
import polars as ps
from pygeoif import Point, Polygon, MultiPolygon
from shapely import (
    Point as sPoint,
    Polygon as sPolygon,
    MultiPolygon as sMultiPolygon,
)
from shapely.geometry import shape


def create_intersections_file(
    isd_geo,
    house_geo,
    senate_geo,
    save_loc: str = "./data/intersections.json",
):
    if not os.path.exists(save_loc):
        isd_2_house, house_2_isd, isd_2_senate, senate_2_isd = create_intersection_map(
            isd_geo, house_geo, senate_geo
        )

        big_map = {
            "ISD to house": isd_2_house,
            "house to ISD": house_2_isd,
            "ISD to senate": isd_2_senate,
            "senate to ISD": senate_2_isd,
        }

        with open(save_loc, "w") as fh:
            json.dump(big_map, fh)
        return big_map
    else:
        with open(save_loc, "r") as fh:
            return json.load(fh)


def create_intersection_map(isd_geo, house_geo, senate_geo):
    """
    Create the adjacency chart that shows which ISDs overlap with
    which senate and house districts. This is, of course, bidirectional
    """
    isd_to_house_intersections = {}
    house_to_isd_intersections = {}
    isd_to_senate_intersections = {}
    senate_to_isd_intersections = {}

    for isd_name, isd_poly in isd_geo:
        for house_name, house_poly in house_geo:
            intersection = isd_poly.intersection(house_poly)
            if not intersection.is_empty:
                house_to_isd_intersections.setdefault(house_name, {})[isd_name] = (
                    intersection.area
                )
                isd_to_house_intersections.setdefault(isd_name, {})[house_name] = (
                    intersection.area
                )

        for senate_name, senate_poly in senate_geo:
            intersection = isd_poly.intersection(senate_poly)
            if not intersection.is_empty:
                senate_to_isd_intersections.setdefault(senate_name, {})[isd_name] = (
                    intersection.area
                )
                isd_to_senate_intersections.setdefault(isd_name, {})[senate_name] = (
                    intersection.area
                )

    return (
        isd_to_house_intersections,
        house_to_isd_intersections,
        isd_to_senate_intersections,
        senate_to_isd_intersections,
    )


def convert_pygeoif_to_shapely(shape):
    if isinstance(shape, Point):
        return sPoint(shape.coords)
    if isinstance(shape, Polygon):
        return sPolygon(shape.coords[0])
    if isinstance(shape, MultiPolygon):
        return sMultiPolygon(
            [convert_pygeoif_to_shapely(subpol) for subpol in shape.geoms]
        )
    raise TypeError(f"conversion not defined for shape of type {type(shape)}")


def extract_isd_geometry(isd_kml: kml.KML):
    return sorted(
        [
            (isd.name, convert_pygeoif_to_shapely(isd.geometry))
            for isd in isd_kml.features[0].features[0].features
        ],
        key=lambda e: e[0],
    )


def extract_lege_geometry(lege_kml: kml.KML):
    geometries = []
    for district in lege_kml.features[0].features:
        for geom in district.geometry.geoms:
            if not isinstance(geom, Point):
                geometries.append((district.name, convert_pygeoif_to_shapely(geom)))

    return sorted(geometries, key=lambda e: e[0])


def _make_process_function(extractor_func, _cache_path: str):

    def _fun(kml_path, cache_path: str = _cache_path):
        if not os.path.exists(cache_path):
            to_json = {}
            isd_kml = kml.KML.parse(kml_path)
            isd_geo = extractor_func(isd_kml)

            for isd_name, isd_poly in isd_geo:
                to_json[isd_name] = isd_poly.__geo_interface__

            with open(cache_path, "w") as fh:
                json.dump(to_json, fh)

        with open(cache_path, "r") as fh:
            from_json = json.load(fh)
            return {key: shape(item) for (key, item) in from_json.items()}

    return _fun


process_isd_kml = _make_process_function(
    extract_isd_geometry, "./data/parsed_isd_kml.json"
)
process_house_kml = _make_process_function(
    extract_lege_geometry, "./data/parsed_house_kml.json"
)
process_senate_kml = _make_process_function(
    extract_lege_geometry, "./data/parsed_senate_kml.json"
)

dont_update_map = False

if __name__ == "__main__":
    app = Dash()
else:
    app = Dash(__name__, requests_pathname_prefix="/isds/")

print("processing KML files")
isd_geo = process_isd_kml("./data/School_Districts_2026.kml")
house_geo = process_house_kml("./data/PlanH2316.kml")
senate_geo = process_senate_kml("./data/PlanS2168.kml")

print("done processing KML. Loading intersections file")
intersections = create_intersections_file(isd_geo, house_geo, senate_geo)
print("loaded intersections file")

print("Loading lege membership CSVs")
house_members_csv = ps.read_csv("./data/house_89th_lege.csv")
senate_members_csv = ps.read_csv("./data/senate_89th_lege.csv")
print("Loaded lege members CSVs")


def main():
    app.layout = [
        html.H1(
            children="ISDs and Legislative Districts", style={"textAlign": "center"}
        ),
        html.H3(
            "select ISD(s) in the map below using any of the selection tools, "
            "and view overlapping house and senate districts in the plots below"
        ),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Dropdown(
                            id="isd-selection-dropdown",
                            options=sorted(isd_geo.keys()),
                            multi=True,
                        ),
                        dcc.Graph(
                            id="isd-selection-graph",
                            figure=show_isd_map(),
                            config={
                                "scrollZoom": True,
                                "modeBarButtonsToAdd": ["zoom2d"],
                            },
                        ),
                    ],
                    style={"width": "750px", "display": "inline-block"},
                ),
            ],
            style={"display": "inline-block"},
        ),
        html.Br(),
        html.Div(
            [
                html.Div(
                    [
                        html.H3("overlapping house districts"),
                        dcc.Graph(id="hd-output-graph"),
                        dash_table.DataTable(
                            id="selected-hd-table",
                            sort_action="native",
                        ),
                    ],
                    style={"display": "inline-block"},
                ),
                html.Div(
                    [
                        html.H3("overlapping senate districts"),
                        dcc.Graph(id="sd-output-graph"),
                        dash_table.DataTable(
                            id="selected-sd-table",
                            sort_action="native",
                        ),
                    ],
                    style={"display": "inline-block"},
                ),
            ]
        ),
    ]


@callback(
    Output("hd-output-graph", "figure", allow_duplicate=True),
    Output("sd-output-graph", "figure", allow_duplicate=True),
    Output("selected-hd-table", "data", allow_duplicate=True),
    Output("selected-sd-table", "data", allow_duplicate=True),
    Output("isd-selection-dropdown", "value"),
    Input("isd-selection-graph", "selectedData"),
    prevent_initial_call=True,
)
def show_isd_map_for_selection(selected_data):
    """
    Update the map to show overlapping senate and house districts based on the
    ISDs that were selected
    """
    if selected_data is None:
        return (
            go.Figure(layout={"width": 450}),
            go.Figure(layout={"width": 450}),
            [],
            [],
            [],
        )

    selected_isds = [elem["location"] for elem in selected_data["points"]]
    hd_fig, sd_fig, hd_rows, sd_rows = _generate_common_selection_outputs(selected_isds)

    global dont_update_map
    dont_update_map = True
    return hd_fig, sd_fig, hd_rows.to_dicts(), sd_rows.to_dicts(), selected_isds


@callback(
    Output("isd-selection-graph", "figure"),
    Output("hd-output-graph", "figure"),
    Output("sd-output-graph", "figure"),
    Output("selected-hd-table", "data"),
    Output("selected-sd-table", "data"),
    Input("isd-selection-dropdown", "value"),
)
def update_isd_map_for_dropdown_selection(selected_isds):
    intersecting_hds = []
    intersecting_sds = []
    if selected_isds is None:
        selected_isds = []
    for isd in selected_isds:
        intersecting_hds.extend(intersections["ISD to house"][isd])
        intersecting_sds.extend(intersections["ISD to senate"][isd])
    intersecting_hds = list(set(intersecting_hds))
    intersecting_sds = list(set(intersecting_sds))

    hd_fig, sd_fig, hd_rows, sd_rows = _generate_common_selection_outputs(selected_isds)
    isd_to_index = {isd: idx for (idx, isd) in enumerate(sorted(isd_geo.keys()))}

    global dont_update_map
    if dont_update_map:
        fig = no_update
        dont_update_map = False
    else:
        fig = show_isd_map()
        fig.update_traces(selectedpoints=[isd_to_index[isd] for isd in selected_isds])

    return (fig, hd_fig, sd_fig, hd_rows.to_dicts(), sd_rows.to_dicts())


def _generate_common_selection_outputs(selected_isds):
    intersecting_hds = []
    intersecting_sds = []
    selected_isds = selected_isds or []

    for isd in selected_isds:
        intersecting_hds.extend(intersections["ISD to house"][isd])
        intersecting_sds.extend(intersections["ISD to senate"][isd])
    intersecting_hds = list(set(intersecting_hds))
    intersecting_sds = list(set(intersecting_sds))

    hd_rows = house_members_csv.filter(
        ps.col("District").is_in({int(n.split()[1]) for n in intersecting_hds})
    )
    sd_rows = senate_members_csv.filter(
        ps.col("District").is_in({int(n.split()[1]) for n in intersecting_sds})
    )

    hd_geojson = convert_polys_to_geojson(
        {hd: house_geo[hd] for hd in intersecting_hds}
    )
    selected_isd_geojson = convert_polys_to_geojson(
        {isd: isd_geo[isd] for isd in selected_isds}
    )
    merged_hd_geojsons = _merge_geojson_dicts(selected_isd_geojson, hd_geojson)
    hd_fig = _make_lege_map_for_selection(
        merged_hd_geojsons, selected_isds, intersecting_hds
    )

    sd_geojson = convert_polys_to_geojson(
        {sd: senate_geo[sd] for sd in intersecting_sds}
    )
    merged_sd_geojsons = _merge_geojson_dicts(selected_isd_geojson, sd_geojson)
    sd_fig = _make_lege_map_for_selection(
        merged_sd_geojsons, selected_isds, intersecting_sds
    )

    return hd_fig, sd_fig, hd_rows, sd_rows


def _make_lege_map_for_selection(hd_geojson, selected_isds, intersecting_hds):
    fig = go.Figure()
    trace = go.Choropleth(
        showscale=False,
        geojson=hd_geojson,
        locations=intersecting_hds + selected_isds,
        z=[2] * len(intersecting_hds) + [1] * len(selected_isds),
        marker={"opacity": 0.25},
    )

    fig.add_trace(trace)
    fig.update_geos(fitbounds="locations")
    fig.update_layout(margin={p: 0 for p in "lrbt"}, height=250, width=450)
    return fig


def show_isd_map():
    print("creating ISD map")
    fig = go.Figure(
        layout={
            "height": 500,
            "width": 900,
            "margin": {p: 0 for p in "lrbt"},
            "autosize": False,
        }
    )
    isd_geojson = convert_polys_to_geojson(isd_geo)
    trace = go.Choropleth(
        showscale=False,
        geojson=isd_geojson,
        locations=list(isd_geo.keys()),
        z=[1] * len(isd_geo),
        marker={"opacity": 0.25},
    )
    fig.add_trace(trace)
    fig.update_geos(fitbounds="locations")
    return fig


def convert_polys_to_geojson(polys):
    features = []
    for key, polygon in polys.items():
        features.append(
            {"type": "Feature", "geometry": polygon.__geo_interface__, "id": key}
        )
    return {"type": "FeatureCollection", "features": features}


def _merge_geojson_dicts(dict1, dict2):
    features = dict1["features"] + dict2["features"]
    return {"type": "FeatureCollection", "features": features}


def plot_polygon(name, shape):
    if isinstance(shape, sPolygon):
        points = np.array(shape.exterior.coords)
        return go.Scattermap(
            lon=points[:, 0],
            lat=points[:, 1],
            marker={"size": 0},
            fill="toself",
            visible="legendonly",
            name=name,
        )
    elif isinstance(shape, sMultiPolygon):
        lons = []
        lats = []

        for subshape in shape.geoms:
            for point in subshape.exterior.coords:
                lons.append(point[0])
                lats.append(point[1])
            lons.append(None)
            lats.append(None)

        if len(lons) > 0:
            lons.pop()
            lats.pop()
        return go.Scattermap(
            lon=lons,
            lat=lats,
            marker={"size": 0},
            fill="toself",
            visible="legendonly",
            name=name,
        )

    raise ValueError(f"no plotting defined for object of type {type(shape)}")


def plot_polygons(polygons):
    lons = []
    lats = []
    for polygon in polygons:
        if isinstance(polygon, sPolygon):
            for point in polygon.exterior.coords:
                lons.append(point[0])
                lats.append(point[1])
            lons.append(None)
            lats.append(None)
        elif isinstance(polygon, sMultiPolygon):
            for shape in polygon.geoms:
                for point in shape.exterior.coords:
                    lons.append(point[0])
                    lats.append(point[1])
                lons.append(None)
                lats.append(None)
        else:
            raise ValueError(
                f"no plotting function defined for object of type {type(polygon)}"
            )
    if len(lons) > 0:
        lons.pop()
        lats.pop()

    return go.Scattermap(
        fill="toself",
        lon=lons,
        lat=lats,
        marker={"size": 0},
    )


if __name__ == "__main__":
    main()
    app.run(debug=True)

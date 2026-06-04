from dash import Dash, html, dcc, callback, Output, Input, no_update, dash_table
import plotly.graph_objects as go
import polars as ps
from shapely.geometry import geo
from . import geo_tools
from . import resources


dont_update_map = False

if __name__ == "__main__":
    app = Dash()
else:
    app = Dash(__name__, requests_pathname_prefix="/isds-to-districts/")


def initialize():
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
                            options=sorted(resources.isd_geo.keys()),
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
        intersecting_hds.extend(resources.intersections["ISD to house"][isd])
        intersecting_sds.extend(resources.intersections["ISD to senate"][isd])
    intersecting_hds = list(set(intersecting_hds))
    intersecting_sds = list(set(intersecting_sds))

    hd_fig, sd_fig, hd_rows, sd_rows = _generate_common_selection_outputs(selected_isds)
    isd_to_index = {
        isd: idx for (idx, isd) in enumerate(sorted(resources.isd_geo.keys()))
    }

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
        intersecting_hds.extend(resources.intersections["ISD to house"][isd])
        intersecting_sds.extend(resources.intersections["ISD to senate"][isd])
    intersecting_hds = list(set(intersecting_hds))
    intersecting_sds = list(set(intersecting_sds))

    hd_rows = resources.house_members_csv.filter(
        ps.col("District").is_in({int(n.split()[1]) for n in intersecting_hds})
    )
    sd_rows = resources.senate_members_csv.filter(
        ps.col("District").is_in({int(n.split()[1]) for n in intersecting_sds})
    )

    hd_geojson = geo_tools.convert_polys_to_geojson(
        {hd: resources.house_geo[hd] for hd in intersecting_hds}
    )
    selected_isd_geojson = geo_tools.convert_polys_to_geojson(
        {isd: resources.isd_geo[isd] for isd in selected_isds}
    )
    merged_hd_geojsons = geo_tools.merge_geojson_dicts(selected_isd_geojson, hd_geojson)
    hd_fig = _make_lege_map_for_selection(
        merged_hd_geojsons, selected_isds, intersecting_hds
    )

    sd_geojson = geo_tools.convert_polys_to_geojson(
        {sd: resources.senate_geo[sd] for sd in intersecting_sds}
    )
    merged_sd_geojsons = geo_tools.merge_geojson_dicts(selected_isd_geojson, sd_geojson)
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
    isd_geojson = geo_tools.convert_polys_to_geojson(resources.isd_geo)
    trace = go.Choropleth(
        showscale=False,
        geojson=isd_geojson,
        locations=list(resources.isd_geo.keys()),
        z=[1] * len(resources.isd_geo),
        marker={"opacity": 0.25},
    )
    fig.add_trace(trace)
    fig.update_geos(fitbounds="locations")
    return fig


if __name__ == "__main__":
    initialize()
    app.run(debug=True)

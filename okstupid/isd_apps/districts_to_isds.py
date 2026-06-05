import itertools

from dash import Dash, html, dcc, callback, Output, Input, dash_table
import plotly.graph_objects as go
import polars as ps

from . import resources, geo_tools

if __name__ == "__main__":
    app = Dash()
else:
    app = Dash(__name__, requests_pathname_prefix="/districts-to-isds/")


def initialize():
    app.layout = [
        html.H1(children="District-to-ISD Selection", style={"textAlign": "center"}),
        html.H3(
            "select a house legislative district in the map below using any "
            "of the selection tools, and view overlapping ISDs in the next plot"
        ),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Dropdown(
                            id="hd-selection-dropdown",
                            options=sorted(resources.house_geo.keys()),
                            multi=True,
                        ),
                        dcc.Graph(
                            id="hd-selection-graph",
                        ),
                    ],
                    style={"width": "750px", "display": "inline-block"},
                )
            ]
        ),
        html.Br(),
        html.Div(
            [
                html.Div(
                    [
                        html.H3("overlapping ISDs"),
                        dcc.Graph(id="isd-output-graph"),
                        dash_table.DataTable(
                            id="selected-hd-table",
                            sort_action="native",
                            style_data={"whiteSpace": "normal", "height": "auto"},
                        ),
                    ]
                )
            ]
        ),
    ]


update_map = True


@callback(
    Output("isd-output-graph", "figure", allow_duplicate=True),
    Output("selected-hd-table", "data", allow_duplicate=True),
    Output("hd-selection-dropdown", "value", allow_duplicate=True),
    Input("hd-selection-graph", "selectedData"),
    prevent_initial_call=True,
)
def update_isd_map_for_hd_map_selection(selected_data):
    """
    Updates the selected ISDs map when an HD selection is made via the map
    """
    if selected_data is None:
        return go.Figure(layout={"width": 900}), [], [], []

    selected_hds = [elem["location"] for elem in selected_data["points"]]
    isd_fig, _, hd_rows = _generate_common_selection_outputs(selected_hds)
    global update_map
    update_map = False
    return (
        isd_fig,
        hd_rows.to_dicts(),
        selected_hds,
    )


@callback(
    Output("isd-output-graph", "figure"),
    Output("selected-hd-table", "data"),
    Output("hd-selection-graph", "figure"),
    Input("hd-selection-dropdown", "value"),
)
def update_hd_map_for_dropdown_selection(selected_hds):
    """
    Update graphics when selection(s) is made via the dropdown menu
    """
    selected_hds = selected_hds or []
    isd_fig, _, hd_rows = _generate_common_selection_outputs(selected_hds)

    all_hd_geojson = geo_tools.convert_polys_to_geojson(resources.house_geo)
    hd_fig = go.Figure()
    hd_trace = go.Choropleth(
        showscale=False,
        geojson=all_hd_geojson,
        locations=list(resources.house_geo.keys()),
        z=[1] * len(resources.house_geo),
        marker={"opacity": 0.25},
    )
    hd_fig.add_trace(hd_trace)
    hd_fig.update_geos(fitbounds="locations")
    hd_to_index = {
        hd: idx for (idx, hd) in enumerate(sorted(resources.house_geo.keys()))
    }
    hd_fig.update_traces(selectedpoints=[hd_to_index[hd] for hd in selected_hds])
    hd_fig.update_layout(width=900, height=500, margin={p: 0 for p in "lrbt"})

    return (
        isd_fig,
        hd_rows.to_dicts(),
        hd_fig,
    )


def _generate_common_selection_outputs(selected_hds):
    selected_hds = selected_hds or []
    intersecting_isds = list(
        set(
            itertools.chain(
                *(
                    resources.intersections["house to ISD"][hd].keys()
                    for hd in selected_hds
                )
            )
        )
    )

    int_key_hd_intersections = {
        int(k.split()[1]): sorted(v.keys())
        for (k, v) in resources.intersections["house to ISD"].items()
    }
    hd_rows = resources.house_members_csv.filter(
        ps.col("District").is_in({int(n.split()[1]) for n in selected_hds})
    )
    hd_rows = hd_rows.with_columns(
        ps.col("District")
        .replace_strict(int_key_hd_intersections, default=[])
        .list.join(",")
        .alias("Intersecting ISDs")
    )

    isd_geojson = geo_tools.convert_polys_to_geojson(
        {isd: resources.isd_geo[isd] for isd in intersecting_isds}
    )
    selected_hd_geojson = geo_tools.convert_polys_to_geojson(
        {hd: resources.house_geo[hd] for hd in selected_hds}
    )
    merged_isd_geojsons = geo_tools.merge_geojson_dicts(
        selected_hd_geojson, isd_geojson
    )
    isd_fig = _make_isd_map_for_selection(
        merged_isd_geojsons, selected_hds, intersecting_isds
    )
    return isd_fig, intersecting_isds, hd_rows


def _make_isd_map_for_selection(geo_jsons, selected_hds, intersecting_isds):
    fig = go.Figure()
    trace = go.Choropleth(
        showscale=False,
        geojson=geo_jsons,
        locations=intersecting_isds + selected_hds,
        z=[2] * len(intersecting_isds) + [1] * len(selected_hds),
        marker={"opacity": 0.25},
    )
    fig.add_trace(trace)
    fig.update_geos(fitbounds="locations")
    fig.update_layout(margin={p: 0 for p in "lrbt"}, height=500, width=900)
    return fig


if __name__ == "__main__":
    initialize()
    app.run(debug=True)

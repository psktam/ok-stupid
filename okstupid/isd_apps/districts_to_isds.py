import json
import os
from fastkml import kml

from shapely.geometry import shape


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


process_isd_kml = _make_process_function(
    extract_isd_geometry, "./data/parsed_isd_kml.json"
)
process_house_kml = _make_process_function(
    extract_lege_geometry, "./data/parsed_house_kml.json"
)
process_senate_kml = _make_process_function(
    extract_lege_geometry, "./data/parsed_senate_kml.json"
)

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

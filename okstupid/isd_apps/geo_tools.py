def convert_polys_to_geojson(polys):
    features = []
    for key, polygon in polys.items():
        features.append(
            {"type": "Feature", "geometry": polygon.__geo_interface__, "id": key}
        )
    return {"type": "FeatureCollection", "features": features}


def merge_geojson_dicts(dict1, dict2):
    features = dict1["features"] + dict2["features"]
    return {"type": "FeatureCollection", "features": features}

import osmium

pbf_dir="\\v0t0081a\kadas\osm\planet-latest.osm.pbf"

fp = os.path.join(pbf_dir, fn)
pbf_bbox_osmium = osmium.io.Reader(fp).header().box()
print pbf_bbox_osmium


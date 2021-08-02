# either output with CSV template (1) or as text file (2)
grype gisops/routing-graph-packager:latest -o template -t /home/nilsnolde/dev/gis-ops/routing-packager/kadas-routing-packager/ciso_reports/csv.tmpl > /home/nilsnolde/dev/gis-ops/routing-packager/kadas-routing-packager/ciso_reports/scan_$(date +"%m-%d-%Y_%T").csv
# grype gisops/routing-graph-packager:latest > /home/nilsnolde/dev/gis-ops/routing-packager/kadas-routing-packager/ciso_reports/scan_$(date +"%m-%d-%Y_%T").txt

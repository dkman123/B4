cd ~/Documents/UrbanTerror43/q3ut4
ls *.pk3 | awk '{ if ($0 !~ /^zUrT43_/ && $0 !~ /^zzz/) print $0 }' > hopper.txt

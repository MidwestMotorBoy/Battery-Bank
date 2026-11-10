# kept where they are on the current board: Tag-Connect footprints (their holes go through the board and the cup side
# was checked against them), the antenna matching network, and the BLE module's decoupling next to them
for r in ('J301','J302','C313','C314','C315','R321','C301','C302','C303','R304'):
    P[r]=db.fp[r]['base']

require("targets.nut");  // written by `pk ingame`: TARGETS, LOOP {x0,x1,y0,y1}, STOP_TILES [[x,y],...]

class PKTest extends GSController {}

function PKTest::Log(msg) { GSLog.Info("PKTEST " + msg); }

function PKTest::Track(cur, a, b) {
  // side of `cur` facing neighbour n: 0=NE(dx-1) 1=SW(dx+1) 2=NW(dy-1) 3=SE(dy+1)
  local sides = [];
  foreach (n in [a, b]) {
    local dx = GSMap.GetTileX(n) - GSMap.GetTileX(cur);
    local dy = GSMap.GetTileY(n) - GSMap.GetTileY(cur);
    sides.append(dx == -1 ? "NE" : dx == 1 ? "SW" : dy == -1 ? "NW" : "SE");
  }
  sides.sort();
  local k = sides[0] + sides[1];
  local map = { NESW = GSRail.RAILTRACK_NE_SW, NWSE = GSRail.RAILTRACK_NW_SE,
                NENW = GSRail.RAILTRACK_NW_NE, SESW = GSRail.RAILTRACK_SW_SE,
                NWSW = GSRail.RAILTRACK_NW_SW, NESE = GSRail.RAILTRACK_NE_SE };
  return map[k];
}

function PKTest::Start() {
  this.Sleep(1);
  GSCompany.ChangeBankBalance(0, 50000000, GSCompany.EXPENSES_OTHER, GSMap.TILE_INVALID);
  local x0 = LOOP.x0, x1 = LOOP.x1, y0 = LOOP.y0, y1 = LOOP.y1;
  local cx = (x0 + x1) / 2;
  // Clear + level in deity mode (no company): this can also remove town houses/roads.
  local a = GSMap.GetTileIndex(x0 - 3, y0 - 3), b = GSMap.GetTileIndex(x1 + 3, y1 + 3);
  for (local x = x0 - 3; x <= x1 + 3; x++) for (local y = y0 - 3; y <= y1 + 3; y++) GSTile.DemolishTile(GSMap.GetTileIndex(x, y));
  GSTile.LevelTiles(a, b);
  local cm = GSCompanyMode(0);
  GSCompany.SetPrimaryLiveryColour(GSCompany.LS_DEFAULT, GSCompany.COLOUR_DARK_BLUE);
  GSCompany.SetSecondaryLiveryColour(GSCompany.LS_DEFAULT, GSCompany.COLOUR_ORANGE);

  // find our engines
  local engines = [];
  foreach (e, _ in GSEngineList(GSVehicle.VT_RAIL)) {
    local name = GSEngine.GetName(e);
    local hit = false;
    if (name != null) foreach (t in TARGETS) if (name.find(t) != null) hit = true;
    if (hit) { engines.append(e); this.Log("engine " + e + " " + name + " buildable=" + GSEngine.IsBuildable(e)); }
  }
  engines.sort();
  if (engines.len() == 0) { this.Log("ERROR no engines match TARGETS"); return; }
  local rt = GSEngine.GetRailType(engines[0]);
  GSRail.SetCurrentRailType(rt);
  this.Log("railtype " + rt + " " + GSRail.GetName(rt));

  // loop rectangle, centred on the map
  // company mode clean-up pass for anything deity mode left (trees etc.)
  for (local x = x0 - 1; x <= x1 + 1; x++) for (local y = y0 - 2; y <= y1 + 1; y++) GSTile.DemolishTile(GSMap.GetTileIndex(x, y));

  local perim = [];
  for (local x = x0; x < x1; x++) perim.append(GSMap.GetTileIndex(x, y0));
  for (local y = y0; y < y1; y++) perim.append(GSMap.GetTileIndex(x1, y));
  for (local x = x1; x > x0; x--) perim.append(GSMap.GetTileIndex(x, y1));
  for (local y = y1; y > y0; y--) perim.append(GSMap.GetTileIndex(x0, y));
  local n = perim.len(), fails = 0;
  for (local i = 0; i < n; i++) {
    local t = this.Track(perim[i], perim[(i + n - 1) % n], perim[(i + 1) % n]);
    if (!GSRail.BuildRailTrack(perim[i], t)) { fails++; this.Log("rail fail " + GSMap.GetTileX(perim[i]) + "," + GSMap.GetTileY(perim[i]) + " " + GSError.GetLastErrorString()); }
  }
  this.Log("loop built, " + n + " tiles, " + fails + " failures");

  // depot north of the top side, connected with a curve
  local tside = GSMap.GetTileIndex(cx, y0);
  local depot = GSMap.GetTileIndex(cx, y0 - 1);
  if (!GSRail.BuildRailDepot(depot, tside)) this.Log("depot fail " + GSError.GetLastErrorString());
  GSRail.BuildRailTrack(tside, GSRail.RAILTRACK_NW_NE);

  // one train made of every matching engine (all liveries side by side)
  local train = GSVehicle.BuildVehicle(depot, engines[0]);
  this.Log("train " + train + " valid=" + GSVehicle.IsValidVehicle(train) + " " + GSError.GetLastErrorString());
  for (local i = 1; i < engines.len(); i++) {
    local v = GSVehicle.BuildVehicle(depot, engines[i]);
    GSVehicle.MoveWagon(v, 0, train, 0);
  }
  GSVehicle.StartStopVehicle(train);
  this.Log("train started, length " + GSVehicle.GetNumWagons(train));

  // Month m (1-based): after day 10, stop the train when its front is on STOP_TILES[m-1].
  // The console script for the 1st of the next month scrolls there and takes the shot.
  local stopped = false;
  while (true) {
    local date = GSDate.GetCurrentDate();
    local day = GSDate.GetDayOfMonth(date);
    local idx = (GSDate.GetMonth(date) - 1) % STOP_TILES.len();
    local target = GSMap.GetTileIndex(STOP_TILES[idx][0], STOP_TILES[idx][1]);
    if (!stopped && day >= 10 && GSVehicle.GetLocation(train) == target) {
      GSVehicle.StartStopVehicle(train); stopped = true;
      this.Log("stopped at " + STOP_TILES[idx][0] + "," + STOP_TILES[idx][1]);
    }
    if (stopped && day < 10) { GSVehicle.StartStopVehicle(train); stopped = false; }
    this.Sleep(1);
  }
}

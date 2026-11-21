require("targets.nut");  // written by `pk ingame`: TARGETS, LOOP {x0,x1,y0,y1}, STOP_TILES [[x,y],...]

class PKTest extends GSController {}

function PKTest::Log(msg) { GSLog.Info("PKTEST " + msg); }

// 2 = every engine can run on `cand` and has power there, 1 = can run, 0 = can't
function PKTest::Fits(engines, cand) {
  foreach (e in engines) {
    if (!GSEngine.CanRunOnRail(e, cand)) return 0;
    if (GSEngine.GetPower(e) > 0 && !GSEngine.HasPowerOnRail(e, cand)) return 1;
  }
  return 2;
}

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
  // engines in TARGETS order (OpenTTD's internal engine ids don't follow GRF item order)
  local engines = [];
  foreach (t in TARGETS) {
    foreach (e, _ in GSEngineList(GSVehicle.VT_RAIL)) {
      local name = GSEngine.GetName(e);
      if (name != null && name.find(t) != null) {
        engines.append(e);
        this.Log("engine " + e + " " + name + " buildable=" + GSEngine.IsBuildable(e));
      }
    }
  }
  if (engines.len() == 0) { this.Log("ERROR no engines match TARGETS"); return; }
  // a track type every target can run on; prefer one that powers them all (catenary
  // for electric locos even when a non-electric control car comes first)
  // Prefer the first target's own railtype (e.g. plain electrified metre gauge rather than
  // the rack variant); otherwise the first railtype that carries and powers every target.
  local rt = -1;
  local own = GSEngine.GetRailType(engines[0]);
  if (this.Fits(engines, own) == 2) rt = own;
  if (rt == -1) foreach (cand, _ in GSRailTypeList()) if (this.Fits(engines, cand) == 2) { rt = cand; break; }
  if (rt == -1) foreach (cand, _ in GSRailTypeList()) if (this.Fits(engines, cand) == 1) { rt = cand; break; }
  if (rt == -1) { this.Log("ERROR no railtype fits all targets"); return; }
  GSRail.SetCurrentRailType(rt);
  this.Log("railtype " + rt + " " + GSRail.GetName(rt));

  // Slope for hill sprites: raise every vertex with x >= RAISE_X by one level. Tiles
  // x = RAISE_X - 1 then slope up along X (both long sides of the loop get a ramp),
  // and everything beyond is flat one level higher.
  if (RAISE_X > 0) {
    local raised = 0;
    for (local x = RAISE_X; x <= x1 + 4; x++) for (local y = y0 - 4; y <= y1 + 4; y++)
      if (GSTile.RaiseTile(GSMap.GetTileIndex(x, y), GSTile.SLOPE_N)) raised++;
    this.Log("raised " + raised + " vertices at x >= " + RAISE_X);
  }

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

  if (SCENE == "infra") this.BuildInfra(rt);

  // one train made of every matching engine (all liveries side by side)
  local train = GSVehicle.BuildVehicle(depot, engines[0]);
  this.Log("train " + train + " valid=" + GSVehicle.IsValidVehicle(train) + " " + GSError.GetLastErrorString());
  for (local i = 1; i < engines.len(); i++) {
    local v = GSVehicle.BuildVehicle(depot, engines[i]);
    // append at the end so the consist keeps TARGETS/engine-id order (loco first)
    if (!GSVehicle.MoveWagon(v, 0, train, GSVehicle.GetNumWagons(train) - 1))
      this.Log("attach fail " + GSEngine.GetName(engines[i]) + " " + GSError.GetLastErrorString());
  }
  GSVehicle.StartStopVehicle(train);
  this.Log("train started, length " + GSVehicle.GetNumWagons(train));

  // Month m (1-based): after day 10, stop the train when its front is on STOP_TILES[m-1].
  // The console script for the 1st of the next month scrolls there and takes the shot.
  // Month m: stop on STOP_TILES[m-1] as soon as the train reaches it; the console script
  // screenshots on the 1st of month m+1, and the train restarts from day 2. (OpenTTD can't
  // shorten months: the calendar advances at most once per tick, and fast-forward is only
  // reachable through the GUI, so one game month ≈ 67 s real time is the floor per shot.)
  local stopped = false, countdown = -1, reversed = false, stop_month = -1;
  while (true) {
    local date = GSDate.GetCurrentDate();
    local day = GSDate.GetDayOfMonth(date);
    local month = GSDate.GetMonth(date);
    local idx = (month - 1) % STOP_TILES.len();
    local target = GSMap.GetTileIndex(STOP_TILES[idx][0], STOP_TILES[idx][1]);
    // When the head (front articulated part) enters the target tile, run a few more
    // ticks so the sprite-carrying middle part is on the tile too, then stop.
    if (!stopped && month != stop_month && countdown < 0 && GSVehicle.GetLocation(train) == target) countdown = STOP_DELAY;
    if (!stopped && countdown == 0) {
      GSVehicle.StartStopVehicle(train); stopped = true; stop_month = month;
      this.Log("stopped at " + STOP_TILES[idx][0] + "," + STOP_TILES[idx][1] + " (head now " +
               GSMap.GetTileX(GSVehicle.GetLocation(train)) + "," + GSMap.GetTileY(GSVehicle.GetLocation(train)) +
               ", leading: " + GSEngine.GetName(GSVehicle.GetWagonEngineType(train, 0)) + ")");
    }
    if (countdown >= 0) countdown--;
    if (stopped && month != stop_month && day >= 2) {
      GSVehicle.StartStopVehicle(train); stopped = false;
      // push-pull check: turn the whole train round once, so the far end leads.
      // OpenTTD only acts on a reverse order while the train is moving.
      if (REVERSE_AT_MONTH > 0 && GSDate.GetMonth(date) == REVERSE_AT_MONTH && !reversed) {
        reversed = true;
        this.Sleep(20);
        this.Log("reverse train: " + GSVehicle.ReverseVehicle(train) + " " + GSError.GetLastErrorString());
      }
    }
    this.Sleep(1);
  }
}


// --- infrastructure scene (pk ingame --scene infra): everything within the fixed camera ----
function PKTest::RackType() {
  foreach (rt, _ in GSRailTypeList()) {
    local name = GSRail.GetName(rt);
    // GetName returns the short name, e.g. "Electrified rack"
    if (name != null && name.find("rack") != null && name.find("lectrified") != null) return rt;
  }
  return -1;
}

function PKTest::Check(what, ok) {
  this.Log((ok ? "infra ok " : "infra FAIL ") + what + (ok ? "" : " " + GSError.GetLastErrorString()));
}

function PKTest::RaiseBlock(x0, x1, y0, y1) {
  for (local x = x0; x <= x1; x++) for (local y = y0; y <= y1; y++)
    GSTile.RaiseTile(GSMap.GetTileIndex(x, y), GSTile.SLOPE_N);
}

function PKTest::BuildInfra(rt) {
  // level crossing: a road across the loop's SE side (straight X track at (32, 34))
  local roads = GSRoadTypeList(GSRoad.ROADTRAMTYPES_ROAD);
  GSRoad.SetCurrentRoadType(roads.Begin());
  this.Check("road crossing", GSRoad.BuildRoad(GSMap.GetTileIndex(32, 32), GSMap.GetTileIndex(32, 37)));

  // rail bridge on flat land, west of the loop
  local bridges = GSBridgeList_Length(4);
  local bridge_type = bridges.Begin();
  local b0 = GSMap.GetTileIndex(27, 33), b1 = GSMap.GetTileIndex(30, 33);
  for (local x = 26; x <= 30; x++) GSTile.DemolishTile(GSMap.GetTileIndex(x, 33));
  this.Check("bridge", GSBridge.BuildBridge(GSVehicle.VT_RAIL, bridge_type, b0, b1));
  GSRail.BuildRailTrack(GSMap.GetTileIndex(26, 33), GSRail.RAILTRACK_NE_SW);

  // tunnel through a small hill on the raised side (one more level at x 35..37, y 28..30)
  this.RaiseBlock(35, 37, 28, 30);
  local t0 = GSMap.GetTileIndex(34, 29);
  local ok = GSTunnel.BuildTunnel(GSVehicle.VT_RAIL, t0);
  this.Check("tunnel", ok);
  if (ok) {
    local t1 = GSTunnel.GetOtherTunnelEnd(t0);
    this.Log("tunnel " + GSMap.GetTileX(t0) + "," + GSMap.GetTileY(t0) + " -> " + GSMap.GetTileX(t1) + "," + GSMap.GetTileY(t1));
  }

  // four depots, one per direction, north of the loop
  local fronts = [[28, 27], [29, 29], [29, 28], [31, 28]];  // NE, SE, SW, NW neighbours
  local tiles = [[28, 28], [29, 28], [30, 28], [31, 29]];
  for (local i = 0; i < 4; i++) {
    local tile = GSMap.GetTileIndex(tiles[i][0], tiles[i][1]);
    GSTile.DemolishTile(tile);
    this.Check("depot " + i, GSRail.BuildRailDepot(tile, GSMap.GetTileIndex(fronts[i][0], fronts[i][1])));
  }

  // rack sections on both ramps of the loop
  local rack = this.RackType();
  this.Check("rack type found", rack != -1);
  if (rack != -1) {
    foreach (t in [[33, 31], [33, 34]]) {
      local tile = GSMap.GetTileIndex(t[0], t[1]);
      this.Check("rack " + t[0] + "," + t[1], GSRail.ConvertRailType(tile, tile, rack));
    }
  }
  GSRail.SetCurrentRailType(rt);
}

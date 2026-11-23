"""The shot lab: a person's shots, played through the real game, from chosen spots.

    gdb -batch -x shotlab.py --args bin/SWOS.x86_64 --renderer=software
    (run by shotlab.sh, which sets the environment below and the game's)

SWOS_SHOOTING_TEST plays SHOOTING PRACTICE: one side against a keeper alone. This script makes
that side player 1's (only its attackers on the pitch), and plays player 1 by writing the
joystick the game reads (`_joy1Dat`, `_ciaa_pra`, at Player1StatusProc): nothing else of the
engine is touched. For each trial it puts the player and the ball on a spot (the one thing a
person could not do), waits for the keeper to settle, then pushes the stick the way of the shot
and holds fire until the game kicks (the shot charges as a held button does), and plays the
trial's aftertouch: the stick it holds at each aftertouch step. What the ball and the keeper do
is the game's. One JSON line per shot goes to LAB_OUT.

LAB_TRIALS    a JSON file: a list of {"id", "spot": [x, y], "dir": 0..7, "at": [10 sticks, -1 none]}
LAB_OUT       where the results go
LAB_KEEPER    the keeper's skill (0..7), LAB_SHOOTING / LAB_FINISHING the shooter's (0..7)
LAB_SETTLE    frames the keeper is given to settle (default 40: he is in place within 15)
LAB_DEBUG     1: a line a frame while a trial runs
"""
import json
import os
import struct

import gdb

TRIALS = json.load(open(os.environ["LAB_TRIALS"]))
OUT = open(os.environ["LAB_OUT"], "a", buffering=1)
KEEPER = int(os.environ.get("LAB_KEEPER", "4"))
SHOOTING = int(os.environ.get("LAB_SHOOTING", "6"))
FINISHING = int(os.environ.get("LAB_FINISHING", "6"))
SETTLE = int(os.environ.get("LAB_SETTLE", "40"))
DEBUG = os.environ.get("LAB_DEBUG") == "1"
TRACE = os.environ.get("LAB_TRACE") == "1"

# The joystick as the Amiga port reads it (src/input.c): right bit 1, left bit 9, down bit 0
# xor bit 1, up bit 8 xor bit 9. Index: the compass direction, 0 up .. 7 up-left; 8 none.
JOY = [0x0100, 0x0103, 0x0003, 0x0002, 0x0001, 0x0301, 0x0300, 0x0200, 0x0000]
DXY = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

T = K = None                   # the player's side and the keeper's (found when the match is on)
WAIT, SETTLE_, SHOOT, FLIGHT = range(4)


def ev(expr):
    return int(gdb.parse_and_eval(expr))


def setv(expr, val):
    gdb.execute(f"set var {expr} = {val}", to_string=True)


_A = {}


def addr(expr):
    if expr not in _A:
        _A[expr] = ev(f"(long)&({expr})")
    return _A[expr]


def rd(expr, fmt="<h"):
    """A field read at its cached address: "<h" a word, "<i" a long, "fx" a FixedPoint's
    whole part."""
    inf = gdb.selected_inferior()
    if fmt == "fx":
        return struct.unpack("<i", bytes(inf.read_memory(addr(expr), 4)))[0] >> 16
    return struct.unpack(fmt, bytes(inf.read_memory(addr(expr), struct.calcsize(fmt))))[0]


def wr(expr, val, fmt="<h"):
    gdb.selected_inferior().write_memory(addr(expr), struct.pack(fmt, val))


class Lab:
    def __init__(self):
        self.n = 0                  # frames of the match
        self.state = WAIT
        self.since = 0
        self.ti = 0                 # the next trial
        self.joy, self.fire = 8, False
        self.addr = None
        self.rec = None
        self.done = False
        self.setup_done = False
        self.forced = 0             # restarts the watchdog had to make
        self.tries = 0              # times the trial was set up (a failed set-up is tried again)

    # ---- the joystick, written where the game reads it ----------------------------------
    def stick(self):
        if T is None:
            return
        wr("_joy1Dat", JOY[self.joy], "<H")
        wr("_ciaa_pra", 0x7F if self.fire else 0xFF, "<B")

    # ---- shooting practice made the player's -------------------------------------------
    def setup(self):
        setv("setup.side[0]", 1)            # MODSIDE_PLAYER1
        setv("setup.linesOut[0]", 3)        # its defence and midfield off: its attackers only
        setv("setup.quickRestarts", 1)
        setv("setup.playingUp", 1)          # the keeper's side at the top: the shots go up, at y 129
        setv("s_shootThrows", 2)            # (the test's own throw-ins and corners: none)
        setv("s_shootCorners", 2)
        setv("'replay_v2.c'::s_rec.suppressed", 1)     # no whole-match recording: a lab session is one
                                                    # match of hours, and its recording grows ~200 MB a minute
        self.setup_done = True
        print("LAB setup", flush=True)

    def skills(self):
        for i in range(16):
            setv(f"{T}.inGameTeamPtr->players[{i}].shooting", SHOOTING)
            setv(f"{T}.inGameTeamPtr->players[{i}].finishing", FINISHING)
        setv(f"{K}.inGameTeamPtr->players[0].goalieSkill", KEEPER)
        setv(f"{K}.shotChanceTable", f"_kGoalieSkillTables[{KEEPER}]")

    # ---- a trial ------------------------------------------------------------------------
    def teleport(self, t):
        x, y = t["spot"]
        d = t["dir"]
        p = None
        for i in range(1, 11):
            s = f"{T}.spritesTable[{i}]"
            if not ev(f"{s}->sentAway"):
                if p is None:
                    p = s
                else:               # the other attackers: out of the way, far down the pitch
                    fx = 80 if i % 2 else 590
                    setv(f"{s}->x.raw", (fx << 16)); setv(f"{s}->y.raw", (740 << 16))
                    setv(f"{s}->destX", fx); setv(f"{s}->destY", 740)
        if p is None:
            return False
        self.pl = p
        self.pin(t)
        setv(f"{T}.controlledPlayer", p)
        setv(f"{T}.spinTimer", -1); setv(f"{K}.spinTimer", -1); setv(f"{T}.passInProgress", 0)
        self.skills()
        self.kp = ev(f"(long){K}.spritesTable[0]")
        return True

    def pin(self, t):
        """The player on the spot, facing the shot, and the ball still at his feet."""
        x, y = t["spot"]
        d, p = t["dir"], self.pl
        setv(f"{p}->x.raw", x << 16); setv(f"{p}->y.raw", y << 16); setv(f"{p}->z.raw", 0)
        setv(f"{p}->destX", x); setv(f"{p}->destY", y); setv(f"{p}->direction", d)
        bx, by = x + 3 * DXY[d][0], y + 3 * DXY[d][1]
        for f, v in (("x.raw", bx << 16), ("y.raw", by << 16), ("z.raw", 0), ("deltaZ.raw", 0),
                     ("speed", 0), ("destX", bx), ("destY", by)):
            setv(f"_ballSprite.{f}", v)

    def start(self):
        t = TRIALS[self.ti]
        self.rec = {"id": t["id"], "tech": t.get("tech"), "target": t.get("target"), "spot": t["spot"],
                    "dir": t["dir"], "at": t["at"], "keeper": KEEPER,
                    "shooting": SHOOTING, "finishing": FINISHING, "events": [], "path": [], "forced": self.forced}
        self.tries += 1
        if self.tries > 4:                  # it could not be set up: on to the next
            self.finish("noposs")
            return False
        if not self.teleport(t):
            self.rec = None
            return False
        self.state, self.since = SETTLE_, self.n
        return True

    def finish(self, result):
        r = self.rec
        r["result"] = result
        OUT.write(json.dumps(r) + "\n")
        self.rec = None
        self.state, self.since = WAIT, self.n
        self.ti += 1
        self.tries = 0
        if self.ti >= len(TRIALS):
            self.done = True

    # ---- each frame ------------------------------------------------------------------------
    def frame(self):
        self.n += 1
        if TRACE:
            gdb.set_convenience_variable("labf", self.n)
        global T, K
        if not self.setup_done:
            return
        if T is None:                       # the keeper's side is the one whose outfielders are away
            if not ev("_topTeamData.spritesTable[5]->sentAway") and not ev("_bottomTeamData.spritesTable[5]->sentAway"):
                return
            T, K = (("_bottomTeamData", "_topTeamData") if ev("_topTeamData.spritesTable[5]->sentAway")
                    else ("_topTeamData", "_bottomTeamData"))
            print(f"LAB player {T}, keeper {K} at y {ev(K + '.spritesTable[0]->y.s.i')}", flush=True)
        if not self.done:
            wr("s_shootFrames", 0, "<i")    # the drill's 6000-frame end: not until we are done
        wr(f"{T}.playerNumber", 1)
        gsp, gs = rd("_gameStatePl"), rd("_gameState")
        el = self.n - self.since
        if self.done:
            wr("s_shootFrames", 6000, "<i")
            self.joy, self.fire = 8, False
            return
        if DEBUG and self.n % 200 == 0:
            print(f"LAB status f={self.n} state={self.state} gsp={gsp} gs={gs} ti={self.ti} "
                  f"ball={rd('_ballSprite.x', 'fx')},{rd('_ballSprite.y', 'fx')} pn={rd(T + '.playerNumber')}",
                  flush=True)
        if self.state == WAIT:
            self.joy, self.fire = 8, False
            if gsp == 100 and gs == 100 and el > 15:
                self.start()
            elif el > 900:                  # a restart that never came: play on from here
                print(f"LAB watchdog f={self.n} ti={self.ti} gsp={gsp} gs={gs} ball={rd('_ballSprite.x', 'fx')},"
                      f"{rd('_ballSprite.y', 'fx')}: forced into play", flush=True)
                wr("_gameStatePl", 100)
                wr("_gameState", 100)
                self.forced += 1
                self.since = self.n
            elif gsp != 100 and el > 30:    # a restart of ours (a kick-off): a kick, any way it may go
                self.joy = (6, 2, 4, 5, 3, 0)[(el // 30) % 6]
                self.fire = 4 <= (el % 30) < 22
                if el > 400:                # (or a tap: a pass)
                    self.fire = 4 <= (el % 30) < (22 if (el // 180) % 2 else 7)
                if el == 401:
                    print(f"LAB waiting f={self.n} ti={self.ti} gsp={gsp} gs={gs} ball={rd('_ballSprite.x', 'fx')},"
                          f"{rd('_ballSprite.y', 'fx')} hasBall={rd(T + '.playerHasBall')}", flush=True)
        elif self.state == SETTLE_:
            self.joy, self.fire = 8, False
            has = rd(f"{T}.playerHasBall")
            if gsp != 100:                  # play stopped (the keeper came for it): set it up again
                self.rec = None
                self.state, self.since = WAIT, self.n
            elif not has and el < 25:       # until he has it, he and the ball stay put
                self.pin(TRIALS[self.ti])
            elif el >= SETTLE and not has:  # he never took it: again
                self.start()
            elif el >= SETTLE:
                self.state, self.since = SHOOT, self.n
                self.rec["start"] = {"n": self.n, "pl": [ev(f"{self.pl}->x.s.i"), ev(f"{self.pl}->y.s.i")],
                                     "ball": [ev("_ballSprite.x.s.i"), ev("_ballSprite.y.s.i")],
                                     "gk": [ev(f"{K}.spritesTable[0]->x.s.i"), ev(f"{K}.spritesTable[0]->y.s.i")],
                                     "has": ev(f"{T}.playerHasBall")}
        elif self.state == SHOOT:
            self.joy, self.fire = self.rec["dir"], True
            if el > 40:
                self.finish("nokick")
        elif self.state == FLIGHT:
            self.fire = False
            st = rd(f"{T}.spinTimer")
            self.joy = self.rec["at"][st] if 0 <= st <= 9 else 8
            if self.joy < 0:
                self.joy = 8
            b = [rd("_ballSprite.x", "fx"), rd("_ballSprite.y", "fx"), rd("_ballSprite.z", "fx")]
            g = [rd(f"((Sprite *){self.kp})->x", "fx"), rd(f"((Sprite *){self.kp})->y", "fx")]
            self.rec["path"].append([self.n] + b + g + [st])
            if "cross" not in self.rec and b[1] <= 129:
                self.rec["cross"] = {"n": self.n, "x": b[0], "y": b[1], "z": b[2]}
            if DEBUG:
                print(f"LAB f={self.n} st={st} joy={self.joy} ball={b} gk={g} gsp={gsp} gs={gs}", flush=True)
            res = self.outcome(gsp, el)
            if res:
                self.finish(res)
        if DEBUG and self.state in (SETTLE_, SHOOT):
            print(f"LAB f={self.n} state={self.state} pl={ev(f'{self.pl}->x.s.i')},{ev(f'{self.pl}->y.s.i')} "
                  f"dir={ev(f'{self.pl}->direction')} ball={ev('_ballSprite.x.s.i')},{ev('_ballSprite.y.s.i')} "
                  f"has={ev(f'{T}.playerHasBall')} gk={ev(f'{K}.spritesTable[0]->x.s.i')},{ev(f'{K}.spritesTable[0]->y.s.i')}", flush=True)

    def outcome(self, gsp, el):
        kinds = [e[0] for e in self.rec["events"]]
        if "goal" in kinds:
            return "goal"
        if "claim" in kinds:
            return "caught"
        saved = "parry" in kinds or "deflect" in kinds
        if "touch" in kinds:
            return "parried" if saved else "touched"
        if gsp != 100:                      # out of play, no goal
            if saved:
                return "parried"
            c = self.rec.get("cross")
            if c and 302 <= c["x"] <= 366:
                return "over"
            return "wide" if c else "out"
        if el > 300:
            return "parried" if ("parry" in kinds or "deflect" in kinds) else "stopped"
        return None

    # ---- events --------------------------------------------------------------------------
    def kick(self):
        if T is None:
            return
        ours = ev(f"team == &{T}")
        if self.state == SHOOT and ours:
            self.rec["kick"] = {"n": self.n, "ball": [ev("_ballSprite.x.s.i"), ev("_ballSprite.y.s.i")],
                                "pl": [ev("player->x.s.i"), ev("player->y.s.i")], "dir": ev("player->direction"),
                                "speed": ev("_ballSprite.speed"), "dest": [ev("_ballSprite.destX"), ev("_ballSprite.destY")],
                                "gk": [ev(f"{K}.spritesTable[0]->x.s.i"), ev(f"{K}.spritesTable[0]->y.s.i")]}
            self.state, self.since = FLIGHT, self.n
        elif self.state == FLIGHT:
            self.event("touch", ours)

    def event(self, kind, *extra):
        if self.state == FLIGHT and self.rec is not None:
            self.rec["events"].append([kind, self.n, ev("_ballSprite.x.s.i"), ev("_ballSprite.y.s.i"),
                                       ev("_ballSprite.z.s.i")] + list(extra))


LAB = Lab()


class Hook(gdb.Breakpoint):
    def __init__(self, spec, fn):
        super().__init__(spec, internal=True)
        self.fn = fn

    def stop(self):
        try:
            self.fn()
        except gdb.error as e:
            print(f"LAB error at {self.location}: {e}", flush=True)
        return False


gdb.execute("set pagination off")
gdb.execute("set confirm off")
gdb.execute("set print thread-events off")
gdb.execute("handle SIGPIPE nostop noprint pass")
gdb.execute("handle SIGUSR1 nostop noprint pass")
gdb.execute("set breakpoint pending on")
Hook("mod_petarku_practice.c:325", LAB.setup)
# Once a frame, as the platform has just read the pads (InputSDL_PostFrame): the lab's turn,
# then the joystick it decided on, over what the platform wrote.
Hook("input_sdl.c:2300", lambda: (LAB.frame(), LAB.stick()))
Hook("ball_possession.c:434", LAB.kick)
Hook("headers.c:226", lambda: LAB.event("touch", "header"))
Hook("headers.c:383", lambda: LAB.event("touch", "header"))
Hook("goal_scored.c:182", lambda: LAB.event("goal"))
Hook("GoalkeeperClaimedTheBall", lambda: LAB.event("claim"))
Hook("GoalkeeperDeflectedBall", lambda: LAB.event("deflect"))
Hook("update_players.c:1290", lambda: LAB.event("parry", "controlled"))
Hook("update_players.c:1319", lambda: LAB.event("parry", "scattered"))
Hook("update_players.c:1208", lambda: LAB.event("contact"))
Hook("GoalkeeperJumping", lambda: LAB.state == FLIGHT and LAB.event("dive", ev("diveDir"), ev("keeper->x.s.i"), ev("keeper->y.s.i")))
Hook("ball_physics.c:912", lambda: LAB.event("post"))
Hook("ball_physics.c:925", lambda: LAB.event("bar"))
# The engine's own log of the shot, as trace4.gdb has it (frame = the lab's, $labf).
if TRACE:
    gdb.execute(r'''dprintf ApplyBallAfterTouch,"AT f=%d spin=%d L=%d R=%d ctrlDir=%d stick=%d ball=%d,%d,%d speed=%d dest=%d,%d dz=%d\n", $labf, team->spinTimer, team->leftSpin, team->rightSpin, team->controlledPlDirection, team->currentAllowedDirection, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i, _ballSprite.speed, _ballSprite.destX, _ballSprite.destY, _ballSprite.deltaZ.raw''')
    gdb.execute("condition $bpnum team->spinTimer >= 0 && team == &_bottomTeamData")
    gdb.execute(r'''dprintf ShouldGoalkeeperDive,"SGD f=%d gk=%d,%d ball=%d,%d,%d defX=%d dist=%d\n", $labf, keeper->x.s.i, keeper->y.s.i, ball->x.s.i, ball->y.s.i, ball->z.s.i, _ballDefensiveX, keeper->ballDistance''')
    gdb.execute(r'''dprintf goalkeeper.c:259,"SGDEND f=%d framesY=%d framesX=%d framesDive=%d\n", $labf, framesY, framesX, framesDive''')
    gdb.execute(r'''dprintf GoalkeeperJumping,"JUMP f=%d dir=%d variant=%d gk=%d,%d ball=%d,%d,%d bspeed=%d dist=%d\n", $labf, diveDir, speedVariant, keeper->x.s.i, keeper->y.s.i, ball->x.s.i, ball->y.s.i, ball->z.s.i, ball->speed, keeper->ballDistance''')
    gdb.execute(r'''dprintf update_players.c:1140,"DIVE f=%d gk=%d,%d gkspeed=%d pw=%d ball=%d,%d,%d\n", $labf, player->x.s.i, player->y.s.i, player->speed, player->imageIndex >= 0 ? ((SpriteGraphics **)_spriteGraphicsPtr)[player->imageIndex]->pixWidth : -1, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i''')
    gdb.execute(r'''dprintf update_players.c:891,"CATCHTEST f=%d gk=%d,%d defZ=%d dist=%d def=%d,%d ball=%d,%d,%d\n", $labf, player->x.s.i, player->y.s.i, _ballDefensiveZ, player->ballDistance, _ballDefensiveX, _ballDefensiveY, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i''')
gdb.execute("run")
gdb.execute("quit")

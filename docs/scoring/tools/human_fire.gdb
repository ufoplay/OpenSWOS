# Load BEFORE trace4.gdb (gdb -x human_fire.gdb -x trace4.gdb ...).
#
# The one-on-one roll (update_players.c, the keeper's update) needs the attacking side's fire
# button DOWN while the ball is within ~11 units of the keeper. The CPU never holds fire there
# (ai.c clears it each update; it presses it only for an odd kick), so in CPU v CPU matches
# the roll never runs. This plays the human's part, and only that: at the roll's fire test,
# when the roll's own other test will pass (the attacker on the ball at the keeper's feet, or a
# shot of his struck in the last 3 team updates: passKickTimer, 25 at a release, >= 22), it holds
# the attacker's fire button -- what a player pressing or still holding fire then does.
# Everything else is the engine's.
set pagination off
break update_players.c:751 if team->opponentsTeam->playerHasBall || team->opponentsTeam->passKickTimer >= 22
commands
silent
printf "HUMANFIRE f=%u attacker=%s finOwn=%d finRead=%d gkskill=%d\n", 'replay_v2.c'::s_rec.frameCount, team->opponentsTeam->inGameTeamPtr->players[team->opponentsTeam->lastHeadingTacklingPlayer ? team->opponentsTeam->lastHeadingTacklingPlayer->playerOrdinal - 1 : 0].shortName, team->opponentsTeam->inGameTeamPtr->players[team->opponentsTeam->lastHeadingTacklingPlayer ? team->opponentsTeam->lastHeadingTacklingPlayer->playerOrdinal - 1 : 0].finishing, team->inGameTeamPtr->players[team->opponentsTeam->lastHeadingTacklingPlayer ? team->opponentsTeam->lastHeadingTacklingPlayer->playerOrdinal - 1 : 0].finishing, team->inGameTeamPtr->players[0].goalieSkill
set var team->opponentsTeam->firePressed = 1
continue
end

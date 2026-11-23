set pagination off
set confirm off
set print thread-events off
handle SIGPIPE nostop noprint pass
handle SIGUSR1 nostop noprint pass

# Every line starts with an event name and f=<recorder frame>, the .SRP frame index.

# A kick, after PlayerKickingBall added (or not) the shot bonus: the play_kick_sample line.
dprintf ball_possession.c:434,"KICK f=%u team=%s name=%s top=%d ord=%d state=%d statePl=%d pen=%d pens=%d pl=%d,%d ball=%d,%d,%d speed=%d dest=%d,%d vel=%d fin=%d oppGK=%d gkpos=%d,%d tick=%d\n", 'replay_v2.c'::s_rec.frameCount, team->inGameTeamPtr->teamName, team->inGameTeamPtr->players[player->playerOrdinal-1].shortName, team == &_topTeamData, player->playerOrdinal, _gameState, _gameStatePl, _penalty, _playingPenalties, player->x.s.i, player->y.s.i, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i, _ballSprite.speed, _ballSprite.destX, _ballSprite.destY, team->inGameTeamPtr->players[player->playerOrdinal-1].shooting, team->inGameTeamPtr->players[player->playerOrdinal-1].finishing, team->opponentsTeam->inGameTeamPtr->players[0].goalieSkill, team->opponentsTeam->spritesTable[0]->x.s.i, team->opponentsTeam->spritesTable[0]->y.s.i, _currentGameTick

# Headers (jump and static), after the heading bonus.
dprintf headers.c:226,"HEADER f=%u kind=jump team=%s name=%s top=%d heading=%d plspeed=%d pl=%d,%d ball=%d,%d,%d speed=%d dz=%d dest=%d,%d dir=%d\n", 'replay_v2.c'::s_rec.frameCount, team->inGameTeamPtr->teamName, team->inGameTeamPtr->players[player->playerOrdinal-1].shortName, team == &_topTeamData, team->inGameTeamPtr->players[player->playerOrdinal-1].heading, player->speed, player->x.s.i, player->y.s.i, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i, _ballSprite.speed, _ballSprite.deltaZ.raw, _ballSprite.destX, _ballSprite.destY, team->controlledPlDirection
dprintf headers.c:383,"HEADER f=%u kind=static team=%s name=%s top=%d heading=%d plspeed=%d pl=%d,%d ball=%d,%d,%d speed=%d dz=%d dest=%d,%d dir=%d\n", 'replay_v2.c'::s_rec.frameCount, team->inGameTeamPtr->teamName, team->inGameTeamPtr->players[player->playerOrdinal-1].shortName, team == &_topTeamData, team->inGameTeamPtr->players[player->playerOrdinal-1].heading, player->speed, player->x.s.i, player->y.s.i, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i, _ballSprite.speed, _ballSprite.deltaZ.raw, _ballSprite.destX, _ballSprite.destY, team->controlledPlDirection

# Aftertouch, every update while the window is open.
dprintf ApplyBallAfterTouch,"AT f=%u top=%d spin=%d L=%d R=%d pass=%d ctrlDir=%d stick=%d ball=%d,%d,%d speed=%d dest=%d,%d dz=%d\n", 'replay_v2.c'::s_rec.frameCount, team == &_topTeamData, team->spinTimer, team->leftSpin, team->rightSpin, team->passInProgress, team->controlledPlDirection, team->currentAllowedDirection, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i, _ballSprite.speed, _ballSprite.destX, _ballSprite.destY, _ballSprite.deltaZ.raw
condition $bpnum team->spinTimer >= 0

# The keeper weighing a dive, and its last test.
dprintf ShouldGoalkeeperDive,"SGD f=%u tick=%d top=%d gk=%d,%d gkdx=%d ball=%d,%d,%d bdy=%d defX=%d dist=%d pen=%d pens=%d\n", 'replay_v2.c'::s_rec.frameCount, _currentGameTick, team == &_topTeamData, keeper->x.s.i, keeper->y.s.i, keeper->deltaX.raw, ball->x.s.i, ball->y.s.i, ball->z.s.i, ball->deltaY.raw, _ballDefensiveX, keeper->ballDistance, _penalty, _playingPenalties
dprintf goalkeeper.c:259,"SGDEND f=%u framesY=%d framesX=%d framesDive=%d\n", 'replay_v2.c'::s_rec.frameCount, framesY, framesX, framesDive

# The dive, the diving body's contact test, a contact.
dprintf GoalkeeperJumping,"JUMP f=%u dir=%d variant=%d gk=%d,%d ball=%d,%d,%d bspeed=%d dist=%d\n", 'replay_v2.c'::s_rec.frameCount, diveDir, speedVariant, keeper->x.s.i, keeper->y.s.i, ball->x.s.i, ball->y.s.i, ball->z.s.i, ball->speed, keeper->ballDistance
dprintf update_players.c:1140,"DIVE f=%u gk=%d,%d gkdx=%d gkspeed=%d state=%d img=%d pw=%d ball=%d,%d,%d bdy=%d\n", 'replay_v2.c'::s_rec.frameCount, player->x.s.i, player->y.s.i, player->deltaX.raw, player->speed, player->playerState, player->imageIndex, player->imageIndex >= 0 ? ((SpriteGraphics **)_spriteGraphicsPtr)[player->imageIndex]->pixWidth : -1, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i, _ballSprite.deltaY.raw
dprintf update_players.c:1208,"CONTACT f=%u ball=%d,%d,%d speed=%d\n", 'replay_v2.c'::s_rec.frameCount, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i, _ballSprite.speed

# The point-blank roll: its inputs, and its two outcomes.
dprintf update_players.c:771,"DUELROLL f=%u tick=%d gk=%d,%d gkskill=%d ball=%d,%d,%d dist=%d attacker=%d\n", 'replay_v2.c'::s_rec.frameCount, _currentGameTick, player->x.s.i, player->y.s.i, team->inGameTeamPtr->players[0].goalieSkill, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i, player->ballDistance, team->opponentsTeam->lastHeadingTacklingPlayer ? team->opponentsTeam->lastHeadingTacklingPlayer->playerOrdinal : 0
dprintf update_players.c:776,"DUEL_BEATEN f=%u\n", 'replay_v2.c'::s_rec.frameCount
dprintf update_players.c:802,"DUEL_SAVED f=%u\n", 'replay_v2.c'::s_rec.frameCount

# The keeper parrying, claiming.
dprintf GoalkeeperDeflectedBall,"DEFLECT f=%u top=%d ball=%d,%d,%d speed=%d savedTimer=%d\n", 'replay_v2.c'::s_rec.frameCount, team == &_topTeamData, ball->x.s.i, ball->y.s.i, ball->z.s.i, ball->speed, team->goalkeeperSavedCommentTimer
dprintf GoalkeeperClaimedTheBall,"CLAIM f=%u top=%d gk=%d,%d ball=%d,%d,%d\n", 'replay_v2.c'::s_rec.frameCount, team == &_topTeamData, keeper->x.s.i, keeper->y.s.i, ball->x.s.i, ball->y.s.i, ball->z.s.i

# A diving contact's outcome: a controlled parry, a scattered parry (the two fall into one
# tail, where the ball's new speed and target are set). A catch is the CLAIM line.
dprintf update_players.c:1290,"PARRY f=%u kind=controlled ball=%d,%d,%d speed=%d dest=%d,%d tick=%d savedTimer=%d\n", 'replay_v2.c'::s_rec.frameCount, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i, _ballSprite.speed, _ballSprite.destX, _ballSprite.destY, _currentGameTick, team->goalkeeperSavedCommentTimer
dprintf update_players.c:1319,"PARRY f=%u kind=scattered ball=%d,%d,%d speed=%d dest=%d,%d tick=%d savedTimer=%d\n", 'replay_v2.c'::s_rec.frameCount, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i, _ballSprite.speed, _ballSprite.destX, _ballSprite.destY, _currentGameTick, team->goalkeeperSavedCommentTimer
dprintf update_players.c:1342,"PARRYOUT f=%u speed=%d dest=%d,%d\n", 'replay_v2.c'::s_rec.frameCount, _ballSprite.speed, _ballSprite.destX, _ballSprite.destY

# The keeper's catch test (goalie_can_catch_checks), with every input it reads.
dprintf update_players.c:891,"CATCHTEST f=%u top=%d gk=%d,%d lastTeamOurs=%d hadBall=%d inGkArea=%d tickHi=%d f3A=%d nextGroundX=%d defZ=%d defZmax=%d dist=%d def=%d,%d ball=%d,%d,%d\n", 'replay_v2.c'::s_rec.frameCount, team == &_topTeamData, player->x.s.i, player->y.s.i, team == _lastTeamPlayed, _playerHadBall, _ballInGoalkeeperArea, (_currentGameTick & 0xF0) >> 4, team->shotChanceTable->field_3A, _ballNextGroundX, _ballDefensiveZ, _gsBallDefensiveZ, player->ballDistance, _ballDefensiveX, _ballDefensiveY, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i

# The woodwork.
dprintf ball_physics.c:912,"POST f=%u ball=%d,%d,%d speed=%d\n", 'replay_v2.c'::s_rec.frameCount, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i, _ballSprite.speed
dprintf ball_physics.c:925,"BAR f=%u ball=%d,%d,%d speed=%d\n", 'replay_v2.c'::s_rec.frameCount, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i, _ballSprite.speed

# A goal: who scored and how the game files it.
dprintf goal_scored.c:182,"GOAL f=%u scoringTeam=%d scorerTeam=%d own=%d scorerTeamName=%s scorer=%s ord=%d pen=%d pens=%d ball=%d,%d,%d\n", 'replay_v2.c'::s_rec.frameCount, scoringTeam, scorerSprite->teamNumber, scorerSprite->teamNumber != scoringTeam, _lastTeamScored->inGameTeamPtr->teamName, _lastTeamScored->inGameTeamPtr->players[scorerSprite->playerOrdinal-1].shortName, scorerSprite->playerOrdinal, _penalty, _playingPenalties, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i

run
quit

set pagination off
set confirm off
set print thread-events off
handle SIGPIPE nostop noprint pass
handle SIGUSR1 nostop noprint pass

# A kick: after PlayerKickingBall added (or not) the shot bonus -- ball_possession.c, not_a_shot.
dprintf ball_possession.c:434,"KICK f=%u tick=%d top=%d ord=%d pl=%d,%d ball=%d,%d,%d speed=%d dest=%d,%d vel=%d fin=%d oppGK=%d gkpos=%d,%d\n", 'replay_v2.c'::s_rec.frameCount, _currentGameTick, team == &_topTeamData, player->playerOrdinal, player->x.s.i, player->y.s.i, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i, _ballSprite.speed, _ballSprite.destX, _ballSprite.destY, team->inGameTeamPtr->players[player->playerOrdinal-1].shooting, team->inGameTeamPtr->players[player->playerOrdinal-1].finishing, team->opponentsTeam->inGameTeamPtr->players[0].goalieSkill, team->opponentsTeam->spritesTable[0]->x.s.i, team->opponentsTeam->spritesTable[0]->y.s.i

# The keeper weighing a dive (every frame the cascade reaches F).
dprintf ShouldGoalkeeperDive,"SGD f=%u tick=%d top=%d gk=%d,%d gkdx=%d ball=%d,%d,%d bdy=%d defX=%d dist=%d\n", 'replay_v2.c'::s_rec.frameCount, _currentGameTick, team == &_topTeamData, keeper->x.s.i, keeper->y.s.i, keeper->deltaX.raw, ball->x.s.i, ball->y.s.i, ball->z.s.i, ball->deltaY.raw, _ballDefensiveX, keeper->ballDistance

# Its last test: frames for the dive vs frames for the ball.
dprintf goalkeeper.c:259,"SGDEND f=%u framesY=%d framesX=%d framesDive=%d\n", 'replay_v2.c'::s_rec.frameCount, framesY, framesX, framesDive

# The dive itself.
dprintf GoalkeeperJumping,"JUMP f=%u dir=%d variant=%d gk=%d,%d ball=%d,%d,%d bspeed=%d dist=%d\n", 'replay_v2.c'::s_rec.frameCount, diveDir, speedVariant, keeper->x.s.i, keeper->y.s.i, ball->x.s.i, ball->y.s.i, ball->z.s.i, ball->speed, keeper->ballDistance

# The point-blank roll's two outcomes.
dprintf update_players.c:776,"DUEL_BEATEN f=%u\n", 'replay_v2.c'::s_rec.frameCount
dprintf update_players.c:802,"DUEL_SAVED f=%u\n", 'replay_v2.c'::s_rec.frameCount

# The diving body touching the ball.
dprintf update_players.c:1208,"CONTACT f=%u\n", 'replay_v2.c'::s_rec.frameCount

# A goal.
dprintf goal_scored.c:188,"GOAL f=%u ball=%d,%d,%d\n", 'replay_v2.c'::s_rec.frameCount, _ballSprite.x.s.i, _ballSprite.y.s.i, _ballSprite.z.s.i

run
quit
